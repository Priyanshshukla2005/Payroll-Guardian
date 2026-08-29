"""AI Anomaly Detection Package for AI Payroll Guardian."""

from ai.detection.anomaly_detector import BaseAnomalyDetector
from ai.detection.autoencoder import TabularAutoencoderDetector
from ai.detection.baseline_rules import DeterministicBaselineDetector
from ai.detection.calibrator import ProbabilityCalibrator
from ai.detection.enhanced_rules import EnhancedRuleDetector
from ai.detection.hybrid_detector import HybridPayrollDetector_V2
from ai.detection.isolation_forest import IsolationForestDetector
from ai.detection.random_forest import RandomForestDetector
from ai.detection.type_classifier import MultiLabelAnomalyTypeClassifier
from ai.detection.xgboost_model import GradientBoostingDetector

__all__ = [
    "BaseAnomalyDetector",
    "IsolationForestDetector",
    "RandomForestDetector",
    "GradientBoostingDetector",
    "TabularAutoencoderDetector",
    "HybridPayrollDetector_V2",
    "MultiLabelAnomalyTypeClassifier",
    "DeterministicBaselineDetector",
    "EnhancedRuleDetector",
    "ProbabilityCalibrator",
]
