"""Deterministic fixtures used only for orchestration tests."""

from typing import Any, Dict

from .dsl_models import SceneRequest


def build_fixture_plan(request: SceneRequest) -> Dict[str, Any]:
    """Build a deterministic scene-plan fixture.

    This function tests orchestration/schema plumbing only. Its output is not
    evidence of LLM generation, renderer execution, or measured quality.
    """

    return {
        "fixture": True,
        "topic": request.topic,
        "duration": request.duration,
        "level": request.level.value,
        "seed": request.seed,
        "scenes": [
            {
                "id": "fixture-01",
                "engine": "manim",
                "purpose": "introduction",
            },
            {
                "id": "fixture-02",
                "engine": "manim",
                "purpose": "core concept",
            },
        ],
    }
