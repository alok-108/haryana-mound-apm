"""
Scoped Benchmark Models for Haryana Mound Prospection:
1. Detectability-Dependent Survey Propensity Estimator (treated as Sensitivity Analysis).
2. Orengo et al. (2020) Random Forest Baseline.
3. Gradient Boosted Decision Tree Baseline (HistGradientBoosting / LightGBM).
4. Propensity-Weighted Non-Negative Positive-Unlabelled (SAR-nnPU) Classifier
   (Kiryo et al. 2017, arXiv:1703.00593; Bekker & Davis 2020, doi:10.1007/s10994-020-05877-5).
5. AlphaEarth 64-D Embedding Prototype Cosine Similarity / k-NN Scorer (with hard-negative suppression).
"""

from __future__ import annotations
from typing import Optional
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

try:
    import lightgbm as _lgb
except ImportError:
    _lgb = None


class DetectabilityCoupledSurveyPropensity:
    """
    Survey Propensity Estimator:
    Models selection propensity e(c) = P(S=1 | Y=1, d_hat_c, map_symbol_c, b_access_c).
    Note: Until real walked-tract boundary polygons are digitized from survey archives,
    this model represents a sensitivity-analysis proxy and is NOT claimed to be fully anchored.
    """

    def __init__(self, min_propensity_clip: float = 0.05) -> None:
        self.min_propensity_clip = min_propensity_clip
        self.scaler = StandardScaler()
        self.model = LogisticRegression(C=1.0, max_iter=500)

    @staticmethod
    def _build_design_matrix(
        detectability_proxy: np.ndarray,
        on_historical_map: np.ndarray,
        accessibility_covariates: np.ndarray,
    ) -> np.ndarray:
        d = np.asarray(detectability_proxy, dtype=np.float64).reshape(-1, 1)
        m = np.asarray(on_historical_map, dtype=np.float64).reshape(-1, 1)
        b = np.asarray(accessibility_covariates, dtype=np.float64)
        if b.ndim == 1:
            b = b.reshape(-1, 1)
        interaction = d * m
        return np.hstack([d, m, interaction, b])

    def fit(
        self,
        detectability_proxy: np.ndarray,
        on_historical_map: np.ndarray,
        accessibility_covariates: np.ndarray,
        target_labels: np.ndarray,
    ) -> "DetectabilityCoupledSurveyPropensity":
        X = self._build_design_matrix(detectability_proxy, on_historical_map, accessibility_covariates)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, target_labels.astype(int))
        return self

    def predict_propensity(
        self,
        detectability_proxy: np.ndarray,
        on_historical_map: np.ndarray,
        accessibility_covariates: np.ndarray,
    ) -> np.ndarray:
        X = self._build_design_matrix(detectability_proxy, on_historical_map, accessibility_covariates)
        X_scaled = self.scaler.transform(X)
        probs = self.model.predict_proba(X_scaled)[:, 1]
        return np.clip(probs, self.min_propensity_clip, 1.0)


def compute_sar_nnpu_risk_and_grad(
    params: np.ndarray,
    X_pos: np.ndarray,
    X_unl: np.ndarray,
    w_pos: np.ndarray,
    prior_pi_p: float = 0.02,
    beta_tolerance: float = 0.0,
    l2_reg: float = 1e-3,
) -> tuple[float, np.ndarray]:
    """
    Exact Propensity-Weighted Non-Negative PU (SAR-nnPU) Risk and Analytical Gradient
    under smooth sigmoid loss l(z, y) = sigmoid(-y * z) in [0, 1].
    References:
    - Kiryo et al. (2017, NeurIPS, arXiv:1703.00593)
    - Bekker & Davis (2020, Machine Learning, doi:10.1007/s10994-020-05877-5)
    """
    d = X_pos.shape[1]
    w = params[:d]
    b = params[d]

    z_p = X_pos @ w + b
    z_u = X_unl @ w + b

    loss_p_plus = expit(-z_p)
    loss_p_minus = expit(z_p)
    loss_u_minus = expit(z_u)

    # Strictly normalize weights so that mean(w_pos) == 1.0
    w_norm = w_pos / (np.mean(w_pos) + 1e-8)

    r_p_plus = float(np.mean(w_norm * loss_p_plus))
    r_p_minus = float(np.mean(w_norm * loss_p_minus))
    r_u_minus = float(np.mean(loss_u_minus))

    neg_risk = r_u_minus - prior_pi_p * r_p_minus

    s_p = loss_p_plus * loss_p_minus
    s_u = expit(-z_u) * loss_u_minus

    grad_r_p_plus_w = -np.mean((w_norm * s_p)[:, None] * X_pos, axis=0)
    grad_r_p_plus_b = float(-np.mean(w_norm * s_p))

    grad_r_p_minus_w = np.mean((w_norm * s_p)[:, None] * X_pos, axis=0)
    grad_r_p_minus_b = float(np.mean(w_norm * s_p))

    grad_r_u_minus_w = np.mean(s_u[:, None] * X_unl, axis=0)
    grad_r_u_minus_b = float(np.mean(s_u))

    # Kiryo et al. 2017 non-negative risk clamping at -beta_tolerance
    if neg_risk < -beta_tolerance:
        clamped_neg_risk = -beta_tolerance
        obj = prior_pi_p * r_p_plus + clamped_neg_risk + 0.5 * l2_reg * float(np.sum(w**2))
        grad_w = prior_pi_p * grad_r_p_plus_w + l2_reg * w
        grad_b = prior_pi_p * grad_r_p_plus_b
    else:
        obj = prior_pi_p * r_p_plus + neg_risk + 0.5 * l2_reg * float(np.sum(w**2))
        grad_w = prior_pi_p * grad_r_p_plus_w + (grad_r_u_minus_w - prior_pi_p * grad_r_p_minus_w) + l2_reg * w
        grad_b = prior_pi_p * grad_r_p_plus_b + (grad_r_u_minus_b - prior_pi_p * grad_r_p_minus_b)

    return float(obj), np.append(grad_w, grad_b)


class TabularNNPUClassifier:
    """
    Propensity-Weighted SAR-nnPU Classifier using L-BFGS-B optimization
    over a random Fourier basis expansion + standardized linear terms.
    """

    def __init__(
        self,
        prior_pi_p: float = 0.02,
        n_rff_components: int = 48,
        beta_tolerance: float = 0.0,
        l2_reg: float = 1e-3,
        max_iter: int = 150,
        random_state: int = 42,
    ) -> None:
        if not (0.0 < prior_pi_p < 0.5):
            raise ValueError(f"Class prior pi_p must be in (0, 0.5), got {prior_pi_p}")
        self.prior_pi_p = float(prior_pi_p)
        self.n_rff_components = n_rff_components
        self.beta_tolerance = beta_tolerance
        self.l2_reg = l2_reg
        self.max_iter = max_iter
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.rff_W_: Optional[np.ndarray] = None
        self.rff_b_: Optional[np.ndarray] = None
        self.params_: Optional[np.ndarray] = None

    def _transform_basis(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        Z = self.scaler.fit_transform(X) if fit else self.scaler.transform(X)
        if fit:
            rng = np.random.default_rng(self.random_state)
            self.rff_W_ = rng.normal(0.0, 1.0 / np.sqrt(Z.shape[1]), size=(Z.shape[1], self.n_rff_components))
            self.rff_b_ = rng.uniform(0.0, 2.0 * np.pi, size=self.n_rff_components)
        rff = np.sqrt(2.0 / self.n_rff_components) * np.cos(Z @ self.rff_W_ + self.rff_b_)
        return np.hstack([Z, rff])

    def fit(
        self,
        X: np.ndarray,
        y_pu: np.ndarray,
        propensity_scores: Optional[np.ndarray] = None,
    ) -> "TabularNNPUClassifier":
        Phi = self._transform_basis(X, fit=True)
        pos_mask = y_pu == 1
        unl_mask = y_pu == 0

        X_pos = Phi[pos_mask]
        X_unl = Phi[unl_mask]

        if propensity_scores is not None:
            raw_w = 1.0 / np.clip(propensity_scores[pos_mask], 0.05, 1.0)
            w_pos = raw_w / (np.mean(raw_w) + 1e-8)
        else:
            w_pos = np.ones(len(X_pos), dtype=np.float64)

        init_params = np.zeros(Phi.shape[1] + 1, dtype=np.float64)
        res = minimize(
            compute_sar_nnpu_risk_and_grad,
            init_params,
            args=(X_pos, X_unl, w_pos, self.prior_pi_p, self.beta_tolerance, self.l2_reg),
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": self.max_iter},
        )
        self.params_ = res.x
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.params_ is None:
            raise RuntimeError("TabularNNPUClassifier not fitted")
        Phi = self._transform_basis(X, fit=False)
        logits = Phi @ self.params_[:-1] + self.params_[-1]
        probs = expit(logits)
        return np.column_stack([1.0 - probs, probs])


class AlphaEarthEmbeddingKNN:
    """
    Competing non-parametric model operating on 64-D unit-norm AlphaEarth vectors (bands A00..A63).
    Computes mean cosine similarity to top-k unexcavated mound prototypes minus similarity
    to hard-negative prototypes (modern brick kilns, dunes, village abadi roofs).
    """

    def __init__(self, k_positives: int = 5, k_hard_negatives: int = 5) -> None:
        self.k_positives = k_positives
        self.k_hard_negatives = k_hard_negatives
        self.pos_vectors: Optional[np.ndarray] = None
        self.neg_vectors: Optional[np.ndarray] = None

    @staticmethod
    def _l2_normalize(E: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(E, axis=1, keepdims=True)
        return E / np.clip(norms, 1e-8, None)

    def fit(
        self,
        E_unexcavated_positives: np.ndarray,
        E_hard_negatives: Optional[np.ndarray] = None,
    ) -> "AlphaEarthEmbeddingKNN":
        if E_unexcavated_positives.shape[1] != 64:
            raise ValueError(f"AlphaEarth embeddings must have 64 bands (A00..A63), got {E_unexcavated_positives.shape[1]}")
        self.pos_vectors = self._l2_normalize(E_unexcavated_positives.astype(np.float64))
        if E_hard_negatives is not None and len(E_hard_negatives) > 0:
            self.neg_vectors = self._l2_normalize(E_hard_negatives.astype(np.float64))
        return self

    def score(self, E_query: np.ndarray) -> np.ndarray:
        if self.pos_vectors is None:
            raise RuntimeError("AlphaEarthEmbeddingKNN not fitted")
        Eq = self._l2_normalize(E_query.astype(np.float64))
        sim_pos = Eq @ self.pos_vectors.T
        k_p = min(self.k_positives, sim_pos.shape[1])
        top_pos = np.mean(np.sort(sim_pos, axis=1)[:, -k_p:], axis=1)

        if self.neg_vectors is not None:
            sim_neg = Eq @ self.neg_vectors.T
            k_n = min(self.k_hard_negatives, sim_neg.shape[1])
            top_neg = np.mean(np.sort(sim_neg, axis=1)[:, -k_n:], axis=1)
            raw = top_pos - 0.5 * np.maximum(0.0, top_neg)
        else:
            raw = top_pos

        return np.clip(0.5 * (raw + 1.0), 0.0, 1.0)


def build_rf_orengo2020_baseline(random_state: int = 42) -> RandomForestClassifier:
    """Random Forest baseline replicating Orengo et al. (2020, PNAS)."""
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=16,
        min_samples_leaf=5,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=random_state,
    )


def build_lightgbm_baseline(random_state: int = 42):
    """Gradient Boosted Decision Tree baseline (uses LightGBM if installed, else HistGradientBoosting)."""
    if _lgb is not None:
        return _lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.03,
            num_leaves=31,
            class_weight="balanced",
            random_state=random_state,
            verbose=-1,
        )
    return HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.03,
        max_leaf_nodes=31,
        class_weight="balanced",
        random_state=random_state,
    )
