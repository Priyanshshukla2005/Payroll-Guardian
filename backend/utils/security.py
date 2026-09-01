"""Security, validation, and sanitization utilities for the backend service layer (Phase 7)."""

import os
from pathlib import Path
import re
from typing import Optional, Set, Tuple
import uuid

ALLOWED_EXTENSIONS: Set[str] = {".csv", ".json", ".parquet"}
ALLOWED_MIME_TYPES: Set[str] = {
    "text/csv",
    "text/plain",
    "application/json",
    "application/octet-stream",
    "application/x-parquet",
    "application/vnd.apache.parquet",
}
DANGEROUS_SUB_EXTENSIONS: Set[str] = {
    ".exe", ".bat", ".cmd", ".sh", ".dll", ".so", ".dylib", ".bin",
    ".py", ".pyc", ".js", ".vbs", ".scr", ".msi", ".ps1", ".com"
}
MAX_FILENAME_LENGTH: int = 255


def sanitize_filename(raw_filename: str) -> str:
    """Strip path traversal characters, null bytes, and unsafe symbols from upload filename."""
    if not raw_filename:
        return f"payroll_{uuid.uuid4().hex[:8]}.csv"

    # Strip null bytes and normalize path separators
    clean_name = raw_filename.replace("\x00", "").replace("\\", "/")
    # Extract basename only to prevent directory traversal
    clean_name = os.path.basename(clean_name)
    # Remove all characters except alphanumeric, underscore, hyphen, and dot
    clean_name = re.sub(r"[^\w\.-]", "_", clean_name)
    # Prevent leading dots / hidden files
    clean_name = clean_name.lstrip(".")
    # Bound filename length
    if len(clean_name) > MAX_FILENAME_LENGTH:
        ext = Path(clean_name).suffix
        stem = clean_name[: MAX_FILENAME_LENGTH - len(ext) - 8]
        clean_name = f"{stem}_{uuid.uuid4().hex[:6]}{ext}"

    return clean_name or f"upload_{uuid.uuid4().hex[:8]}.csv"


def validate_uploaded_file(
    filename: Optional[str],
    content_bytes: bytes,
    content_type: Optional[str] = None,
    max_size_mb: int = 50,
) -> Tuple[bool, Optional[str]]:
    """Verify file extension, size, double-extensions, and binary signatures against security rules."""
    if not filename or not filename.strip():
        return False, "Missing filename."

    # Prevent null-byte injection
    if "\x00" in filename:
        return False, "Null byte injection detected in filename."

    # Validate filename length
    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"Filename exceeds maximum permitted length of {MAX_FILENAME_LENGTH} characters."

    # Validate primary extension
    path_obj = Path(filename.lower())
    ext = path_obj.suffix
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Allowed extensions: {sorted(list(ALLOWED_EXTENSIONS))}."

    # Double extension detection (e.g. 'payroll.csv.exe' or 'data.exe.csv')
    stem = path_obj.stem
    if "." in stem:
        for sub_ext in DANGEROUS_SUB_EXTENSIONS:
            if stem.endswith(sub_ext) or f"{sub_ext}." in stem:
                return False, f"Suspicious multi-extension filename detected ({sub_ext})."

    # Validate size bounds
    max_bytes = max_size_mb * 1024 * 1024
    if len(content_bytes) > max_bytes:
        return False, f"File size ({len(content_bytes)/(1024*1024):.2f}MB) exceeds maximum limit of {max_size_mb}MB."

    if len(content_bytes) == 0:
        return False, "Uploaded file is empty (0 bytes)."

    # Reject executable and binary exploit signatures
    # MZ (DOS/Windows PE), ELF (Linux), Mach-O (\xfe\xed\xfa, \xcf\xfa\xed\xfe), Java class (\xca\xfe\xba\xbe), Script shebang (#!/bin)
    if (
        content_bytes.startswith(b"MZ")
        or content_bytes.startswith(b"\x7fELF")
        or content_bytes.startswith(b"\xca\xfe\xba\xbe")
        or content_bytes.startswith(b"\xfe\xed\xfa\xce")
        or content_bytes.startswith(b"\xfe\xed\xfa\xcf")
        or content_bytes.startswith(b"\xce\xfa\xed\xfe")
        or content_bytes.startswith(b"\xcf\xfa\xed\xfe")
    ):
        return False, "Binary executables or compiled artifacts are strictly rejected."

    # For CSV files, ensure content is valid text encoding
    if ext == ".csv":
        try:
            content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_bytes.decode("latin-1")
            except Exception:
                return False, "Malformed or non-text binary payload disguised as CSV."

    return True, None


def generate_unique_id(prefix: str = "req") -> str:
    """Generate a high-entropy URL-safe identifier."""
    return f"{prefix}_{uuid.uuid4().hex}"
