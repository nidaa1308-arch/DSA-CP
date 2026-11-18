"""
Mathematical Coordinate Registration & Spatial Warping Engine.
Provides:
  - RANSAC Inlier consensus estimation
  - 6-Parameter Affine Transformation (Metric Coordinates)
  - Regularized Thin Plate Spline (TPS) with Tikhonov regularization
  - Held-out out-of-sample Cross-Validated RMSE
"""

from __future__ import annotations
import math
import random
from typing import Any, Callable, Optional
import numpy as np


def _tps_kernel(r: float) -> float:
    """TPS radial basis function: U(r) = r^2 * log(r) for r > 0, else 0."""
    if r < 1e-9:
        return 0.0
    return r * r * math.log(r)


def solve_affine_metric(src_pts: np.ndarray, tgt_pts: np.ndarray) -> tuple[Callable[[tuple[float, float]], tuple[float, float]], np.ndarray]:
    """
    Fit 2D affine transformation: Tgt = A * Src + t.
    Returns (transform_fn, affine_matrix_3x3).
    """
    n = len(src_pts)
    if n < 3:
        # Translation fallback
        shift = np.mean(tgt_pts - src_pts, axis=0) if n > 0 else np.zeros(2)
        return (lambda p: (p[0] + shift[0], p[1] + shift[1])), np.eye(3)

    # Design matrix: [x, y, 1]
    M = np.hstack([src_pts, np.ones((n, 1))])
    # Solve M * params = tgt_pts
    params, _, _, _ = np.linalg.lstsq(M, tgt_pts, rcond=None)
    # params shape: (3, 2)
    # [a, c]
    # [b, d]
    # [tx, ty]

    def transform(p: tuple[float, float]) -> tuple[float, float]:
        v = np.array([p[0], p[1], 1.0])
        res = v @ params
        return (float(res[0]), float(res[1]))

    matrix_3x3 = np.eye(3)
    matrix_3x3[:2, :2] = params[:2, :].T
    matrix_3x3[:2, 2] = params[2, :]

    return transform, matrix_3x3


def solve_tps_metric(
    src_pts: np.ndarray,
    tgt_pts: np.ndarray,
    regularization_lambda: float = 0.01
) -> Callable[[tuple[float, float]], tuple[float, float]]:
    """
    Fit regularized Thin Plate Spline (TPS) in metric coordinate space.
    Minimizes bending energy with Tikhonov regularization lambda * I along the diagonal of K.
    """
    n = len(src_pts)
    if n < 3:
        fn, _ = solve_affine_metric(src_pts, tgt_pts)
        return fn

    # 1. Build K matrix (n x n)
    K = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            r = np.linalg.norm(src_pts[i] - src_pts[j])
            u = _tps_kernel(r)
            K[i, j] = u
            K[j, i] = u

    # Add regularization along diagonal
    K += regularization_lambda * np.eye(n)

    # 2. Build P matrix (n x 3): [1, x, y]
    P = np.hstack([np.ones((n, 1)), src_pts])

    # 3. Assemble full system matrix L of size (n+3) x (n+3)
    # L = [[K, P], [P.T, 0]]
    top = np.hstack([K, P])
    bot = np.hstack([P.T, np.zeros((3, 3))])
    L = np.vstack([top, bot])

    # 4. Target vectors Y of size (n+3) x 2
    Y = np.vstack([tgt_pts, np.zeros((3, 2))])

    # Solve L * W = Y
    try:
        W = np.linalg.solve(L, Y)
    except np.linalg.LinAlgError:
        W, _, _, _ = np.linalg.lstsq(L, Y, rcond=None)

    w_weights = W[:n, :]       # (n, 2)
    affine_weights = W[n:, :]  # (3, 2)

    def tps_transform(p: tuple[float, float]) -> tuple[float, float]:
        px, py = p
        # Affine base: c + a*x + b*y
        out_x = affine_weights[0, 0] + affine_weights[1, 0] * px + affine_weights[2, 0] * py
        out_y = affine_weights[0, 1] + affine_weights[1, 1] * px + affine_weights[2, 1] * py

        # Kernel contributions
        for i in range(n):
            r = math.hypot(px - src_pts[i, 0], py - src_pts[i, 1])
            u = _tps_kernel(r)
            out_x += w_weights[i, 0] * u
            out_y += w_weights[i, 1] * u

        return (float(out_x), float(out_y))

    return tps_transform


class RegistrationService:
    @staticmethod
    def run_ransac(
        src_points: np.ndarray,
        tgt_points: np.ndarray,
        inlier_threshold_m: float = 2.0,
        max_iterations: int = 400,
    ) -> dict[str, Any]:
        """
        RANSAC consensus estimation on matched control points.
        Identifies inliers and eliminates spatial outlier correspondences.
        """
        n = len(src_points)
        if n < 3:
            return {
                "inlier_indices": list(range(n)),
                "inlier_count": n,
                "inlier_ratio": 1.0,
                "iterations": 0,
            }

        best_inliers = []
        rng = random.Random(42)

        for it in range(max_iterations):
            # Sample 3 random points
            sample_idx = rng.sample(range(n), 3)
            try:
                fn, _ = solve_affine_metric(src_points[sample_idx], tgt_points[sample_idx])
            except Exception:
                continue

            inliers = []
            for i in range(n):
                pred = fn((src_points[i, 0], src_points[i, 1]))
                err = math.hypot(pred[0] - tgt_points[i, 0], pred[1] - tgt_points[i, 1])
                if err <= inlier_threshold_m:
                    inliers.append(i)

            if len(inliers) > len(best_inliers):
                best_inliers = inliers
                if len(best_inliers) >= n * 0.95:
                    break

        inlier_ratio = len(best_inliers) / n if n > 0 else 0.0
        return {
            "inlier_indices": sorted(best_inliers),
            "inlier_count": len(best_inliers),
            "inlier_ratio": round(inlier_ratio, 4),
            "iterations": it + 1,
        }

    @classmethod
    def register_and_evaluate(
        cls,
        correspondences: list[dict[str, Any]],
        model_type: str = "tps",
        inlier_threshold_m: float = 2.0,
    ) -> dict[str, Any]:
        """
        Full registration pipeline:
          1. Extract eligible control points
          2. Run RANSAC to detect inliers
          3. Fit requested model (TPS or Affine) on inliers
          4. Compute in-sample AND held-out (cross-validated) RMSE
        """
        # Filter eligible correspondences
        valid_pairs = [c for c in correspondences if c.get("eligible_for_registration") and c.get("cad_centroid") and c.get("drone_centroid")]

        if len(valid_pairs) < 3:
            return {
                "success": False,
                "error": "Insufficient valid control point correspondences for registration (minimum 3 required).",
                "model_used": "none",
                "inliers_count": len(valid_pairs),
                "in_sample_rmse_m": None,
                "held_out_rmse_m": None,
                "transform_fn": lambda p: p,
            }

        src_pts = np.array([c["cad_centroid"] for c in valid_pairs], dtype=float)
        tgt_pts = np.array([c["drone_centroid"] for c in valid_pairs], dtype=float)
        n = len(src_pts)

        # 1. RANSAC Inlier filtering
        ransac_res = cls.run_ransac(src_pts, tgt_pts, inlier_threshold_m=inlier_threshold_m)
        inlier_idx = ransac_res["inlier_indices"]

        if len(inlier_idx) < 3:
            inlier_idx = list(range(n))

        src_inliers = src_pts[inlier_idx]
        tgt_inliers = tgt_pts[inlier_idx]

        # 2. Held-out Cross-Validation (80% train / 20% test split)
        rng = random.Random(77)
        indices = list(range(len(src_inliers)))
        rng.shuffle(indices)
        split = max(2, int(len(src_inliers) * 0.8))
        train_idx = indices[:split]
        test_idx = indices[split:] if len(indices) > split else indices

        # Fit on train split
        if model_type == "tps" and len(train_idx) >= 3:
            eval_fn = solve_tps_metric(src_inliers[train_idx], tgt_inliers[train_idx])
            chosen_model = "Thin Plate Spline (TPS)"
        else:
            eval_fn, _ = solve_affine_metric(src_inliers[train_idx], tgt_inliers[train_idx])
            chosen_model = "Affine (6-Parameter)"

        # Compute held-out RMSE
        held_out_errors = []
        for idx in test_idx:
            pred = eval_fn((src_inliers[idx, 0], src_inliers[idx, 1]))
            err = math.hypot(pred[0] - tgt_inliers[idx, 0], pred[1] - tgt_inliers[idx, 1])
            held_out_errors.append(err * err)

        held_out_rmse = round(math.sqrt(sum(held_out_errors) / len(held_out_errors)), 3) if held_out_errors else None

        # 3. Final model fit on ALL inliers
        if model_type == "tps" and len(src_inliers) >= 3:
            final_fn = solve_tps_metric(src_inliers, tgt_inliers)
        else:
            final_fn, _ = solve_affine_metric(src_inliers, tgt_inliers)

        # Compute in-sample RMSE
        in_sample_errors = []
        for i in range(len(src_inliers)):
            pred = final_fn((src_inliers[i, 0], src_inliers[i, 1]))
            err = math.hypot(pred[0] - tgt_inliers[i, 0], pred[1] - tgt_inliers[i, 1])
            in_sample_errors.append(err * err)

        in_sample_rmse = round(math.sqrt(sum(in_sample_errors) / len(in_sample_errors)), 3) if in_sample_errors else None

        return {
            "success": True,
            "model_used": chosen_model,
            "total_correspondences": n,
            "inliers_count": len(src_inliers),
            "inlier_ratio": ransac_res["inlier_ratio"],
            "in_sample_rmse_m": in_sample_rmse,
            "held_out_rmse_m": held_out_rmse,
            "transform_fn": final_fn,
        }
