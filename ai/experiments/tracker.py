"""Lightweight JSON/CSV experiment tracking module for AI Payroll Guardian."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from pydantic import BaseModel, Field


class ExperimentRecord(BaseModel):
    """Container for a single model experiment run."""

    experiment_id: str
    timestamp: str
    model_name: str
    dataset_version: str = "v1.0-synthetic-dev"
    features_version: str = "66-features-v1"
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    threshold: float = 0.5
    training_time_sec: float = 0.0
    inference_time_ms: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    pr_auc: float = 0.0
    roc_auc: float = 0.0
    false_positives: int = 0
    false_negatives: int = 0
    unique_emp_fp_per_1000: float = 0.0
    notes: Optional[str] = None


class ExperimentTracker:
    """Logs and persists experiment records to experiments/ directory."""

    def __init__(self, experiments_dir: Optional[Union[str, Path]] = None):
        if experiments_dir:
            self.experiments_dir = Path(experiments_dir)
        else:
            self.experiments_dir = Path("experiments")

        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.json_file = self.experiments_dir / "experiments.json"
        self.csv_file = self.experiments_dir / "experiments.csv"
        self.records: List[ExperimentRecord] = []
        self._load_existing()

    def _load_existing(self):
        """Load prior runs from JSON if available."""
        if self.json_file.exists():
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.records = [ExperimentRecord(**item) for item in data]
            except Exception:
                self.records = []

    def log_experiment(self, record: ExperimentRecord) -> ExperimentRecord:
        """Append a new experiment record and persist to disk."""
        self.records.append(record)
        # Save JSON
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in self.records], f, indent=2)

        # Save CSV
        df = pd.DataFrame([r.model_dump() for r in self.records])
        df.to_csv(self.csv_file, index=False)
        return record

    def get_leaderboard(self) -> pd.DataFrame:
        """Return pandas DataFrame summary sorted by F1 score descending."""
        if not self.records:
            return pd.DataFrame()
        df = pd.DataFrame([r.model_dump() for r in self.records])
        return df.sort_values(by="f1_score", ascending=False).reset_index(drop=True)
