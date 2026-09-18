"""Dependency-light contract for public QA field semantics."""

from orchestrator.core.dsl_models import FrameAnalysis, QualityMetrics


def test_quality_metrics_expose_measurements_not_unimplemented_interpretations() -> None:
    assert set(QualityMetrics.model_fields) == {
        "reference_ssim",
        "sharpness_variance",
        "edge_density",
        "clipping_fraction",
        "block_boundary_ratio",
    }

    forbidden = {
        "optical_flow_stability",
        "text_legibility",
        "color_accuracy",
        "motion_artifacts",
    }
    assert forbidden.isdisjoint(QualityMetrics.model_fields)


def test_frame_analysis_names_combined_value_as_heuristic() -> None:
    assert "heuristic_score" in FrameAnalysis.model_fields
    assert "overall_score" not in FrameAnalysis.model_fields
