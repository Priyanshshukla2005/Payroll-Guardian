"""Tabular Autoencoder reconstruction anomaly detector for AI Payroll Guardian.

Learns low-dimensional latent representation of normal payroll behavior.
Reconstruction Mean Squared Error (MSE) serves as the anomaly score.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from ai.detection.anomaly_detector import BaseAnomalyDetector


class PyTorchAutoencoderModule(nn.Module):
    """Feedforward neural autoencoder architecture."""

    def __init__(self, input_dim: int, latent_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.1),
            nn.Linear(32, latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.1),
            nn.Linear(32, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Linear(64, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstruction = self.decoder(latent)
        return reconstruction


class TabularAutoencoderDetector(BaseAnomalyDetector):
    """Reconstruction-based anomaly detector using PyTorch neural autoencoder."""

    def __init__(
        self,
        latent_dim: int = 16,
        epochs: int = 15,
        batch_size: int = 256,
        learning_rate: float = 0.003,
        random_state: int = 42,
    ):
        super().__init__(name="Autoencoder", model_type="reconstruction")
        self.latent_dim = latent_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.net: Optional[PyTorchAutoencoderModule] = None
        self.mse_min_: float = 0.0
        self.mse_max_: float = 1.0

    def fit(
        self,
        X: Union[pd.DataFrame, np.ndarray],
        y: Optional[Union[pd.Series, np.ndarray]] = None,
    ) -> "TabularAutoencoderDetector":
        """Train autoencoder strictly on normal payroll records (y == 0)."""
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        if isinstance(X, pd.DataFrame):
            self.feature_names_in_ = X.columns.tolist()
            X_mat = X.values.astype(np.float32)
        else:
            X_mat = np.asarray(X, dtype=np.float32)

        # Train exclusively on normal instances
        if y is not None:
            y_arr = np.asarray(y)
            normal_mask = (y_arr == 0)
            X_train_norm = X_mat[normal_mask] if np.any(normal_mask) else X_mat
        else:
            X_train_norm = X_mat

        input_dim = X_train_norm.shape[1]
        self.net = PyTorchAutoencoderModule(input_dim=input_dim, latent_dim=self.latent_dim).to(self.device)

        dataset = TensorDataset(torch.from_numpy(X_train_norm))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, drop_last=len(dataset) > self.batch_size)

        optimizer = torch.optim.AdamW(self.net.parameters(), lr=self.learning_rate, weight_decay=1e-4)
        criterion = nn.MSELoss()

        self.net.train()
        for epoch in range(self.epochs):
            for batch in loader:
                x_b = batch[0].to(self.device)
                optimizer.zero_grad()
                recon = self.net(x_b)
                loss = criterion(recon, x_b)
                loss.backward()
                optimizer.step()

        self.is_fitted = True

        # Calculate baseline reconstruction error bounds on training normal samples
        train_mse = self.predict_score(X_train_norm)
        self.mse_min_ = float(np.percentile(train_mse, 1))
        self.mse_max_ = float(np.percentile(train_mse, 99))
        if self.mse_max_ <= self.mse_min_:
            self.mse_max_ = self.mse_min_ + 1.0

        return self

    def predict_score(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute reconstruction Mean Squared Error (MSE) for each sample."""
        if not self.is_fitted or self.net is None:
            raise RuntimeError("Autoencoder must be fitted before computing reconstruction scores.")

        X_mat = X.values.astype(np.float32) if isinstance(X, pd.DataFrame) else np.asarray(X, dtype=np.float32)
        self.net.eval()
        with torch.no_grad():
            x_t = torch.from_numpy(X_mat).to(self.device)
            # Process in sub-batches if large
            recon_t = self.net(x_t)
            mse = torch.mean((recon_t - x_t) ** 2, dim=1).cpu().numpy()

        return mse

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Compute normalized reconstruction error pseudo-score bounded in [0, 1]."""
        mse_scores = self.predict_score(X)
        denom = max(self.mse_max_ - self.mse_min_, 1e-6)
        pseudo_prob = np.clip((mse_scores - self.mse_min_) / denom, 0.0, 1.0)
        p_normal = 1.0 - pseudo_prob
        return np.column_stack([p_normal, pseudo_prob])
