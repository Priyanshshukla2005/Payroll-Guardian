"""Deterministic Database Seeding for Development and Demo Environments (Phase 10)."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from backend.auth.security import get_password_hash
from backend.config.settings import settings
from backend.database.models import ComplianceSource, User
from backend.database.session import SessionLocal, init_db
from backend.dependencies.services import ModelManager

logger = logging.getLogger("payroll_guardian.db.seed")

DEFAULT_USERS = [
    {
        "username": "admin",
        "email": "admin@payrollguardian.internal",
        "password": os.getenv("SEED_ADMIN_PASSWORD", "AdminPassword2026!"),
        "role": "ADMIN",
        "full_name": "Executive System Administrator",
    },
    {
        "username": "payroll_admin",
        "email": "payroll_admin@payrollguardian.internal",
        "password": os.getenv("SEED_PAYROLL_ADMIN_PASSWORD", "PayrollAdmin2026!"),
        "role": "PAYROLL_ADMIN",
        "full_name": "Senior Payroll Officer",
    },
    {
        "username": "auditor",
        "email": "auditor@payrollguardian.internal",
        "password": os.getenv("SEED_AUDITOR_PASSWORD", "Auditor2026!"),
        "role": "AUDITOR",
        "full_name": "Compliance & Statutory Auditor",
    },
    {
        "username": "viewer",
        "email": "viewer@payrollguardian.internal",
        "password": os.getenv("SEED_VIEWER_PASSWORD", "Viewer2026!"),
        "role": "VIEWER",
        "full_name": "Read-Only Stakeholder",
    },
]


def seed_users() -> None:
    """Seed default system users if they do not exist."""
    with SessionLocal() as db:
        for u in DEFAULT_USERS:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"],
                    full_name=u["full_name"],
                    is_active=True,
                )
                db.add(user)
                logger.info(f"Seeded user '{u['username']}' with role '{u['role']}'.")
        db.commit()


def seed_compliance_sources() -> None:
    """Seed statutory knowledge documents and hashes from registry.json."""
    registry_file = settings.raw_knowledge_dir.parent / "metadata" / "registry.json"
    if not registry_file.exists():
        return

    try:
        with open(registry_file, "r", encoding="utf-8") as f:
            registry = json.load(f)

        with SessionLocal() as db:
            for doc_id, doc_meta in registry.items():
                existing = db.query(ComplianceSource).filter(ComplianceSource.document_id == doc_id).first()
                if not existing:
                    source = ComplianceSource(
                        document_id=doc_id,
                        title=doc_meta.get("title", doc_id),
                        source_name=doc_meta.get("source_name"),
                        source_type=doc_meta.get("source_type", "STATUTE"),
                        authority_level=doc_meta.get("authority_level", "AUTHORITATIVE"),
                        jurisdiction=doc_meta.get("jurisdiction", "INDIA"),
                        topic=doc_meta.get("topic"),
                        effective_from=doc_meta.get("effective_from"),
                        effective_until=doc_meta.get("effective_until"),
                        document_version=doc_meta.get("document_version", "v1.0"),
                        file_hash=doc_meta.get("file_hash", "0000"),
                        content_hash=doc_meta.get("content_hash", "0000"),
                        source_url=doc_meta.get("source_url"),
                        status=doc_meta.get("status", "ACTIVE"),
                    )
                    db.add(source)
            db.commit()
            logger.info("Compliance sources seeded successfully.")
    except Exception as e:
        logger.warning(f"Failed to seed compliance sources: {e}")


def seed_database(force_demo: bool = False) -> None:
    """Master seeding entrypoint."""
    init_db()

    # Never seed demo users or data automatically in strict production environments
    if settings.app_env == "production" and not force_demo:
        logger.info("Production environment detected. Skipping automatic dev database seeding.")
        return

    logger.info("Seeding development & demo database records...")
    seed_users()
    seed_compliance_sources()

    # Seed canonical demo analysis anl_demo_202406
    try:
        from backend.database.repository import DatabaseAnalysisRepository
        from backend.services.demo_service import ensure_demo_analysis

        repo = DatabaseAnalysisRepository()
        model_mgr = ModelManager.get_instance()
        model_mgr.initialize()
        ensure_demo_analysis(repo=repo, model_manager=model_mgr)
        logger.info("Canonical demo analysis 'anl_demo_202406' verified in persistent database.")
    except Exception as e:
        logger.warning(f"Could not initialize demo analysis during seed: {e}")
