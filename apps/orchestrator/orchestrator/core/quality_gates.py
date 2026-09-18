"""Measured frame statistics and reference-based video quality gates.

The module deliberately separates direct measurements from interpretation.
Single-frame statistics are never labeled as OCR/text legibility, optical-flow
stability, temporal motion quality, or calibrated color accuracy.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from skimage import metrics as sk_metrics

from .dsl_models import FrameAnalysis, QualityIssue, QualityMetrics
from .observability import RetryableOperation, operation_duration_seconds, process_manager

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Compute bounded image statistics and an explicitly heuristic gate score."""

    def __init__(self) -> None:
        self.quality_thresholds = {
            "reference_ssim_minimum": 0.85,
            "sharpness_variance_minimum": 25.0,
            "clipping_fraction_maximum": 0.05,
            "block_boundary_ratio_maximum": 2.5,
        }

    def set_quality_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Update only threshold keys understood by this analyzer."""

        for key in self.quality_thresholds:
            if key in thresholds:
                self.quality_thresholds[key] = float(thresholds[key])

    def analyze_frame(
        self,
        frame_path: Path,
        reference_path: Optional[Path] = None,
        frame_index: int = 0,
        timestamp: float = 0.0,
    ) -> FrameAnalysis:
        """Measure one frame and optionally compare it with a reference frame."""

        with operation_duration_seconds.labels(operation="frame_analysis").time():
            try:
                frame = self._load_frame(frame_path)
                if frame is None:
                    raise ValueError(f"Could not load frame: {frame_path}")

                issues: List[QualityIssue] = []
                reference_ssim: Optional[float] = None

                if reference_path is not None:
                    reference = self._load_frame(reference_path)
                    if reference is None:
                        issues.append(
                            QualityIssue(
                                type="reference_unreadable",
                                severity="critical",
                                description=f"Could not load reference frame: {reference_path}",
                                suggestion="Provide a readable reference image with matching dimensions.",
                            )
                        )
                    elif reference.shape != frame.shape:
                        issues.append(
                            QualityIssue(
                                type="reference_shape_mismatch",
                                severity="critical",
                                description=(
                                    f"Reference shape {reference.shape} does not match frame shape {frame.shape}; "
                                    "SSIM was not computed."
                                ),
                                suggestion="Compare frames with identical dimensions and channel layout.",
                            )
                        )
                    else:
                        reference_ssim = self._calculate_ssim(frame, reference)
                        threshold = self.quality_thresholds["reference_ssim_minimum"]
                        if reference_ssim < threshold:
                            issues.append(
                                QualityIssue(
                                    type="reference_ssim",
                                    severity="high" if reference_ssim < 0.70 else "medium",
                                    description=(
                                        f"Reference SSIM {reference_ssim:.3f} is below the configured "
                                        f"threshold {threshold:.3f}."
                                    ),
                                    suggestion="Inspect the produced frame against the intended reference.",
                                )
                            )

                gray = self._to_gray(frame)
                sharpness_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                edge_density = self._edge_density(gray)
                clipping_fraction = self._clipping_fraction(frame)
                block_boundary_ratio = self._block_boundary_ratio(gray)

                sharpness_min = self.quality_thresholds["sharpness_variance_minimum"]
                if sharpness_variance < sharpness_min:
                    issues.append(
                        QualityIssue(
                            type="low_spatial_detail",
                            severity="medium",
                            description=(
                                f"Laplacian variance {sharpness_variance:.2f} is below the configured "
                                f"sharpness heuristic {sharpness_min:.2f}."
                            ),
                            suggestion="Inspect the frame for blur or intentionally low-detail content.",
                        )
                    )

                clipping_max = self.quality_thresholds["clipping_fraction_maximum"]
                if clipping_fraction > clipping_max:
                    issues.append(
                        QualityIssue(
                            type="pixel_clipping",
                            severity="medium",
                            description=(
                                f"Clipped-channel fraction {clipping_fraction:.3%} exceeds the configured "
                                f"threshold {clipping_max:.3%}."
                            ),
                            suggestion="Inspect whether extreme black/white values are intentional.",
                        )
                    )

                block_max = self.quality_thresholds["block_boundary_ratio_maximum"]
                if block_boundary_ratio > block_max:
                    issues.append(
                        QualityIssue(
                            type="block_boundary_discontinuity",
                            severity="medium",
                            description=(
                                f"8x8 boundary discontinuity ratio {block_boundary_ratio:.3f} exceeds "
                                f"the configured heuristic {block_max:.3f}."
                            ),
                            suggestion="Inspect the frame for block-like encoding artifacts.",
                        )
                    )

                metrics = QualityMetrics(
                    reference_ssim=reference_ssim,
                    sharpness_variance=sharpness_variance,
                    edge_density=edge_density,
                    clipping_fraction=clipping_fraction,
                    block_boundary_ratio=block_boundary_ratio,
                )

                return FrameAnalysis(
                    frame_index=frame_index,
                    timestamp=timestamp,
                    metrics=metrics,
                    issues=issues,
                    heuristic_score=self._heuristic_score(metrics),
                    analysis_duration=0.0,
                )
            except Exception as exc:
                logger.exception("Frame analysis failed for %s", frame_path)
                return FrameAnalysis(
                    frame_index=frame_index,
                    timestamp=timestamp,
                    metrics=QualityMetrics(
                        reference_ssim=None,
                        sharpness_variance=0.0,
                        edge_density=0.0,
                        clipping_fraction=0.0,
                        block_boundary_ratio=0.0,
                    ),
                    issues=[
                        QualityIssue(
                            type="analysis_error",
                            severity="critical",
                            description=f"Quality analysis failed: {exc}",
                            suggestion="Check frame format and accessibility.",
                        )
                    ],
                    heuristic_score=0.0,
                    analysis_duration=0.0,
                )

    @staticmethod
    def _load_frame(path: Path) -> Optional[np.ndarray]:
        """Load a frame through OpenCV without silently fabricating fallback data."""

        if not path.exists() or not path.is_file():
            return None
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        return frame if frame is not None and frame.size > 0 else None

    @staticmethod
    def _to_gray(frame: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame

    @classmethod
    def _calculate_ssim(cls, first: np.ndarray, second: np.ndarray) -> float:
        """Calculate reference SSIM only for equal-shaped frames."""

        if first.shape != second.shape:
            raise ValueError("SSIM requires equal-shaped frames")
        first_gray = cls._to_gray(first)
        second_gray = cls._to_gray(second)
        return float(
            sk_metrics.structural_similarity(
                first_gray,
                second_gray,
                data_range=255,
            )
        )

    @staticmethod
    def _edge_density(gray: np.ndarray) -> float:
        edges = cv2.Canny(gray, 100, 200)
        return float(np.count_nonzero(edges) / edges.size) if edges.size else 0.0

    @staticmethod
    def _clipping_fraction(frame: np.ndarray) -> float:
        if not frame.size:
            return 0.0
        clipped = (frame <= 1) | (frame >= 254)
        return float(np.count_nonzero(clipped) / frame.size)

    @staticmethod
    def _block_boundary_ratio(gray: np.ndarray) -> float:
        """Compare 8x8-boundary discontinuities with non-boundary differences.

        This is a blockiness heuristic, not a codec diagnosis. A value near 1
        means 8x8 boundaries are not unusually discontinuous relative to other
        adjacent-pixel differences.
        """

        if gray.shape[0] < 9 or gray.shape[1] < 9:
            return 0.0

        values = gray.astype(np.float32)
        vertical = np.abs(np.diff(values, axis=1))
        horizontal = np.abs(np.diff(values, axis=0))

        v_mask = np.zeros(vertical.shape[1], dtype=bool)
        h_mask = np.zeros(horizontal.shape[0], dtype=bool)
        v_mask[np.arange(7, vertical.shape[1], 8)] = True
        h_mask[np.arange(7, horizontal.shape[0], 8)] = True

        boundary_parts = []
        interior_parts = []
        if np.any(v_mask):
            boundary_parts.append(vertical[:, v_mask].ravel())
            interior_parts.append(vertical[:, ~v_mask].ravel())
        if np.any(h_mask):
            boundary_parts.append(horizontal[h_mask, :].ravel())
            interior_parts.append(horizontal[~h_mask, :].ravel())

        if not boundary_parts or not interior_parts:
            return 0.0

        boundary = np.concatenate(boundary_parts)
        interior = np.concatenate(interior_parts)
        boundary_mean = float(np.mean(boundary)) if boundary.size else 0.0
        interior_mean = float(np.mean(interior)) if interior.size else 0.0
        if boundary_mean == 0.0 and interior_mean == 0.0:
            return 0.0
        return boundary_mean / max(interior_mean, 1e-6)

    def _heuristic_score(self, metrics: QualityMetrics) -> float:
        """Combine declared heuristics without presenting them as a calibrated quality metric."""

        sharpness_component = metrics.sharpness_variance / (metrics.sharpness_variance + 100.0)

        clipping_limit = max(self.quality_thresholds["clipping_fraction_maximum"], 1e-6)
        clipping_component = max(0.0, 1.0 - metrics.clipping_fraction / clipping_limit)

        block_limit = max(self.quality_thresholds["block_boundary_ratio_maximum"], 1.000001)
        if metrics.block_boundary_ratio <= 1.0:
            block_component = 1.0
        else:
            block_component = max(
                0.0,
                1.0 - (metrics.block_boundary_ratio - 1.0) / (block_limit - 1.0),
            )

        if metrics.reference_ssim is None:
            score = (sharpness_component + clipping_component + block_component) / 3.0
        else:
            score = (
                0.50 * metrics.reference_ssim
                + 0.20 * sharpness_component
                + 0.15 * clipping_component
                + 0.15 * block_component
            )
        return float(min(1.0, max(0.0, score)))


class VmafAnalyzer:
    """Reference-based VMAF adapter executed through FFmpeg/libvmaf."""

    @RetryableOperation.with_backoff(max_attempts=2)
    async def calculate_vmaf(
        self,
        reference_video: Path,
        distorted_video: Path,
        model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        """Calculate VMAF only when both real input videos are available."""

        if not reference_video.exists() or not distorted_video.exists():
            return {}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            log_path = Path(handle.name)

        model_arg = f"model={model_path}" if model_path else "model=version=vmaf_v0.6.1"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(distorted_video),
            "-i",
            str(reference_video),
            "-lavfi",
            f"libvmaf={model_arg}:log_fmt=json:log_path={log_path}",
            "-f",
            "null",
            "-",
        ]

        try:
            result = await process_manager.run_with_timeout(
                cmd,
                timeout=300.0,
                process_id=f"vmaf_{distorted_video.stem}",
            )
            if result.returncode != 0 or not log_path.exists() or log_path.stat().st_size == 0:
                return {}

            with log_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            scores = [
                float(frame["metrics"]["vmaf"])
                for frame in data.get("frames", [])
                if "vmaf" in frame.get("metrics", {})
            ]
            if not scores:
                return {}

            return {
                "vmaf_mean": float(np.mean(scores)),
                "vmaf_min": float(np.min(scores)),
                "vmaf_max": float(np.max(scores)),
                "vmaf_std": float(np.std(scores)),
                "frame_count": float(len(scores)),
            }
        except Exception:
            logger.exception("VMAF calculation failed")
            return {}
        finally:
            log_path.unlink(missing_ok=True)


class QualityGate:
    """Apply declared heuristics and reference metrics without inventing success."""

    def __init__(self, config: Dict[str, float]):
        self.thresholds = config
        self.analyzer = QualityAnalyzer()
        self.analyzer.set_quality_thresholds(config)
        self.vmaf_analyzer = VmafAnalyzer()

    async def check_frame_sequence(
        self,
        frames: List[Path],
        reference_frames: Optional[List[Path]] = None,
    ) -> Tuple[bool, List[FrameAnalysis]]:
        """Evaluate frame statistics; an empty sequence never passes."""

        if not frames:
            return False, []

        analyses: List[FrameAnalysis] = []
        for index, frame_path in enumerate(frames):
            reference = (
                reference_frames[index]
                if reference_frames is not None and index < len(reference_frames)
                else None
            )
            analyses.append(
                self.analyzer.analyze_frame(
                    frame_path,
                    reference,
                    frame_index=index,
                    timestamp=index / 30.0,
                )
            )

        critical_failures = sum(
            1
            for analysis in analyses
            for issue in analysis.issues
            if issue.severity == "critical"
        )
        average_heuristic = float(np.mean([analysis.heuristic_score for analysis in analyses]))
        minimum = self.thresholds.get("heuristic_score_minimum", 0.60)
        return critical_failures == 0 and average_heuristic >= minimum, analyses

    async def check_video_quality(
        self,
        video_path: Path,
        reference_path: Optional[Path] = None,
    ) -> Dict[str, Union[None, bool, float, str, Dict[str, float], List[str]]]:
        """Run reference-based VMAF or explicitly report that evaluation is unavailable."""

        if not video_path.exists():
            return {
                "evaluation_status": "error",
                "gate_passed": False,
                "vmaf_scores": {},
                "issues": [f"Video does not exist: {video_path}"],
                "vmaf_normalized": None,
            }

        if reference_path is None:
            return {
                "evaluation_status": "not_evaluated",
                "gate_passed": None,
                "vmaf_scores": {},
                "issues": ["Reference video required for VMAF evaluation."],
                "vmaf_normalized": None,
            }

        if not reference_path.exists():
            return {
                "evaluation_status": "error",
                "gate_passed": False,
                "vmaf_scores": {},
                "issues": [f"Reference video does not exist: {reference_path}"],
                "vmaf_normalized": None,
            }

        scores = await self.vmaf_analyzer.calculate_vmaf(reference_path, video_path)
        if not scores:
            return {
                "evaluation_status": "error",
                "gate_passed": False,
                "vmaf_scores": {},
                "issues": ["VMAF could not be computed; verify FFmpeg/libvmaf and input compatibility."],
                "vmaf_normalized": None,
            }

        mean_score = float(scores["vmaf_mean"])
        minimum = self.thresholds.get("vmaf_minimum", 70.0)
        passed = mean_score >= minimum
        return {
            "evaluation_status": "evaluated",
            "gate_passed": passed,
            "vmaf_scores": scores,
            "issues": [] if passed else [f"VMAF {mean_score:.1f} is below threshold {minimum:.1f}."],
            "vmaf_normalized": min(1.0, max(0.0, mean_score / 100.0)),
        }


quality_analyzer = QualityAnalyzer()
default_quality_gate = QualityGate(
    {
        "reference_ssim_minimum": 0.85,
        "sharpness_variance_minimum": 25.0,
        "clipping_fraction_maximum": 0.05,
        "block_boundary_ratio_maximum": 2.5,
        "heuristic_score_minimum": 0.60,
        "vmaf_minimum": 70.0,
    }
)
