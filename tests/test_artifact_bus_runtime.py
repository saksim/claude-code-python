"""Runtime tests for P2-02 artifact bus schema and merge semantics."""

from __future__ import annotations

import pytest

from claude_code.services.artifact_bus import (
    ArtifactBus,
    ArtifactConflictError,
    ArtifactSchemaError,
)


def test_artifact_bus_schema_validation_rejects_invalid_type():
    bus = ArtifactBus()
    with pytest.raises(ArtifactSchemaError, match="type must be one of"):
        bus.publish(
            node_id="n1",
            payload={
                "artifacts": [
                    {"type": "unknown", "key": "x", "content": "v"},
                ]
            },
        )


def test_artifact_bus_producer_consumer_dependency_view():
    bus = ArtifactBus()
    bus.publish(
        node_id="producer",
        payload={
            "artifacts": [
                {"type": "report", "key": "summary", "content": "done"},
                {"type": "note", "key": "ops", "content": "remember"},
            ]
        },
    )

    view = bus.build_dependency_view(["producer"])
    assert "producer" in view
    bundle = view["producer"]
    assert "artifacts" in bundle
    assert "merged" in bundle
    assert bundle["merged"]["report:summary"] == "done"
    assert bundle["merged"]["note:ops"] == "remember"


def test_artifact_bus_append_merge_strategy_collects_conflicts():
    bus = ArtifactBus()
    bus.publish(
        node_id="n1",
        payload={"artifacts": [{"type": "finding", "key": "lint", "content": "E1"}]},
    )
    bus.publish(
        node_id="n2",
        payload={
            "artifacts": [
                {"type": "finding", "key": "lint", "content": "E2", "merge": "append"}
            ]
        },
    )
    snapshot = bus.snapshot()
    assert snapshot["merged"]["finding:lint"] == ["E1", "E2"]


def test_artifact_bus_conflict_fail_strategy_raises():
    bus = ArtifactBus()
    bus.publish(
        node_id="a",
        payload={"artifacts": [{"type": "patch", "key": "fileA", "content": "v1"}]},
    )
    with pytest.raises(ArtifactConflictError, match="artifact conflict"):
        bus.publish(
            node_id="b",
            payload={"artifacts": [{"type": "patch", "key": "fileA", "content": "v2"}]},
        )
