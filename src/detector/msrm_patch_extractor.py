"""
MSRM & DEM Patch Extractor for Tell Morphology Analysis.
Extracts normalized 32x32 pixel spatial patches (~960m x 960m at 30m resolution)
centered on candidate coordinates for CNN shape verification.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.ndimage import gaussian_filter


class MSRMPatchExtractor:
    """
    Extracts standardized 32x32 micro-topographic patches centered on candidates.
    Computes geometric tell morphology indicators (radial symmetry, summit prominence).
    """

    def __init__(self, patch_size: int = 32, pixel_size_m: float = 30.0) -> None:
        self.patch_size = patch_size
        self.pixel_size_m = pixel_size_m
        self.half_size = patch_size // 2

    def extract_patch_from_raster(
        self,
        raster: np.ndarray,
        center_row: int,
        center_col: int,
    ) -> np.ndarray:
        """
        Extract patch with border padding.
        """
        h, w = raster.shape
        r0 = center_row - self.half_size
        r1 = center_row + self.half_size
        c0 = center_col - self.half_size
        c1 = center_col + self.half_size

        pad_top = max(0, -r0)
        pad_bottom = max(0, r1 - h)
        pad_left = max(0, -c0)
        pad_right = max(0, c1 - w)

        if any([pad_top, pad_bottom, pad_left, pad_right]):
            padded = np.pad(
                raster,
                ((pad_top, pad_bottom), (pad_left, pad_right)),
                mode="reflect",
            )
            r0_p = r0 + pad_top
            r1_p = r1 + pad_top
            c0_p = c0 + pad_left
            c1_p = c1 + pad_left
            patch = padded[r0_p:r1_p, c0_p:c1_p]
        else:
            patch = raster[r0:r1, c0:c1]

        # Standardize patch to zero mean, unit variance
        p_std = float(np.std(patch))
        if p_std > 1e-6:
            norm_patch = (patch - float(np.mean(patch))) / p_std
        else:
            norm_patch = patch - float(np.mean(patch))

        return norm_patch.astype(np.float32)

    def synthesize_candidate_patch(
        self,
        estimated_relief_m: float,
        is_linear_embankment: bool = False,
        is_sand_dune: bool = False,
        noise_level: float = 0.15,
        random_state: Optional[int] = None,
    ) -> np.ndarray:
        """
        Synthesize realistic micro-topographic patch based on geomorphic parameters.
        Used for training/evaluating the shape filter when raw raster tiles are not mounted.
        """
        rng = np.random.default_rng(random_state)
        y, x = np.ogrid[:self.patch_size, :self.patch_size]
        cy, cx = self.half_size, self.half_size

        if is_linear_embankment:
            # Linear ridge (canal spoil bank, railway embankment, modern road)
            dist_line = np.abs((x - cx) * 0.8 + (y - cy) * 0.6)
            profile = estimated_relief_m * np.exp(-(dist_line**2) / 12.0)
        elif is_sand_dune:
            # Asymmetric dune with steep slip face
            dist_x = (x - cx)
            dist_y = (y - cy)
            profile = estimated_relief_m * np.exp(-((dist_x * 0.4)**2 + (dist_y * 1.5)**2) / 25.0)
            # Add ripple texture
            profile += 0.3 * np.sin(x * 0.8)
        else:
            # Ancient Tell: Elliptical / circular Gaussian mound with flat summit
            dist_sq = (x - cx)**2 + (y - cy)**2
            radius_px = max(3.0, min(estimated_relief_m * 2.5, 10.0))
            profile = estimated_relief_m * np.exp(-dist_sq / (2.0 * (radius_px**2)))

        patch = profile + rng.normal(0.0, noise_level * max(1.0, estimated_relief_m), size=(self.patch_size, self.patch_size))
        patch_smooth = gaussian_filter(patch, sigma=0.8)

        # Standardize
        p_std = float(np.std(patch_smooth))
        if p_std > 1e-6:
            return ((patch_smooth - float(np.mean(patch_smooth))) / p_std).astype(np.float32)
        return patch_smooth.astype(np.float32)

    @staticmethod
    def compute_morphological_shape_metrics(patch: np.ndarray) -> Dict[str, float]:
        """
        Compute analytical morphological metrics on a 2D patch:
        - Summit prominence
        - Radial symmetry ratio (circularity vs linearity)
        - Peripheral gradient
        """
        h, w = patch.shape
        cy, cx = h // 2, w // 2

        # 1. Summit vs periphery
        center_val = float(patch[cy - 2 : cy + 3, cx - 2 : cx + 3].mean())
        outer_mask = np.ones((h, w), dtype=bool)
        outer_mask[cy - 6 : cy + 7, cx - 6 : cx + 7] = False
        periphery_val = float(patch[outer_mask].mean())
        summit_prominence = center_val - periphery_val

        # 2. Linearity / Radial Symmetry via second moments
        y, x = np.ogrid[:h, :w]
        weights = np.maximum(0.0, patch - periphery_val)
        w_sum = float(weights.sum()) + 1e-8
        
        mu_x = float((x * weights).sum() / w_sum)
        mu_y = float((y * weights).sum() / w_sum)
        
        var_xx = float(((x - mu_x)**2 * weights).sum() / w_sum)
        var_yy = float(((y - mu_y)**2 * weights).sum() / w_sum)
        var_xy = float(((x - mu_x) * (y - mu_y) * weights).sum() / w_sum)

        # Eigenvalues of inertia tensor
        cov = np.array([[var_xx, var_xy], [var_xy, var_yy]])
        eigvals = np.linalg.eigvalsh(cov)
        eigvals = np.maximum(eigvals, 1e-6)
        aspect_ratio = float(np.sqrt(eigvals[1] / eigvals[0]))

        return {
            "summit_prominence": round(summit_prominence, 3),
            "aspect_ratio": round(aspect_ratio, 3),
            "radial_symmetry_score": round(float(np.clip(1.0 / aspect_ratio, 0.05, 1.0)), 3),
        }
