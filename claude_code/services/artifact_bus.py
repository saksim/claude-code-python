"""Artifact bus for multi-agent workflow output exchange and merge control."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class ArtifactSchemaError(ValueError):
    """Raised when an artifact payload fails schema validation."""


class ArtifactConflictError(RuntimeError):
    """Raised when artifact merge policy rejects a conflict."""


class ArtifactType(Enum):
    """Supported artifact categories for multi-agent workflows."""

    PATCH = "patch"
    NOTE = "note"
    DIFF = "diff"
    REPORT = "report"
    FINDING = "finding"


class ArtifactMergeStrategy(Enum):
    """Conflict policy used when two artifacts target the same key."""

    FAIL = "fail"
    APPEND = "append"
    REPLACE = "replace"


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    """Canonical artifact record stored on the artifact bus."""

    artifact_id: str
    node_id: str
    artifact_type: ArtifactType
    key: str
    content: Any
    merge_strategy: ArtifactMergeStrategy = ArtifactMergeStrategy.FAIL
    ownership: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
        *,
        node_id: str,
        index: int,
        default_ownership: tuple[str, ...] = (),
    ) -> "ArtifactRecord":
        """Build one validated artifact record from raw payload."""
        if not isinstance(payload, dict):
            raise ArtifactSchemaError(f"artifact[{index}] must be an object")

        artifact_type_raw = str(payload.get("type") or "").strip().lower()
        if not artifact_type_raw:
            raise ArtifactSchemaError(f"artifact[{index}].type is required")
        try:
            artifact_type = ArtifactType(artifact_type_raw)
        except ValueError as exc:
            supported = ", ".join(item.value for item in ArtifactType)
            raise ArtifactSchemaError(
                f"artifact[{index}].type must be one of: {supported}"
            ) from exc

        key = str(payload.get("key") or "").strip()
        if not key:
            raise ArtifactSchemaError(f"artifact[{index}].key is required")

        has_content = "content" in payload
        has_value = "value" in payload
        if not has_content and not has_value:
            raise ArtifactSchemaError(f"artifact[{index}].content is required")
        content = payload.get("content", payload.get("value"))

        merge_raw = str(payload.get("merge") or payload.get("merge_strategy") or "fail").strip().lower()
        try:
            merge_strategy = ArtifactMergeStrategy(merge_raw)
        except ValueError as exc:
            supported = ", ".join(item.value for item in ArtifactMergeStrategy)
            raise ArtifactSchemaError(
                f"artifact[{index}].merge must be one of: {supported}"
            ) from exc

        ownership_raw = payload.get("ownership", default_ownership)
        ownership = _coerce_string_tuple(
            ownership_raw,
            field_name=f"artifact[{index}].ownership",
        )

        metadata_raw = payload.get("metadata", {})
        if metadata_raw is None:
            metadata = {}
        elif isinstance(metadata_raw, dict):
            metadata = dict(metadata_raw)
        else:
            raise ArtifactSchemaError(f"artifact[{index}].metadata must be an object")

        created_at_raw = payload.get("created_at")
        if created_at_raw is None:
            created_at = time.time()
        else:
            try:
                created_at = float(created_at_raw)
            except Exception as exc:
                raise ArtifactSchemaError(
                    f"artifact[{index}].created_at must be a number"
                ) from exc

        artifact_id = str(payload.get("id") or f"{node_id}:{artifact_type.value}:{key}:{index}")

        return cls(
            artifact_id=artifact_id,
            node_id=node_id,
            artifact_type=artifact_type,
            key=key,
            content=content,
            merge_strategy=merge_strategy,
            ownership=ownership,
            metadata=metadata,
            created_at=created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize artifact record into JSON-safe dict."""
        return {
            "id": self.artifact_id,
            "node_id": self.node_id,
            "type": self.artifact_type.value,
            "key": self.key,
            "content": self.content,
            "merge": self.merge_strategy.value,
            "ownership": list(self.ownership),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


class ArtifactBus:
    """In-memory artifact exchange bus with schema and conflict control."""

    def __init__(self) -> None:
        self._records_by_node: dict[str, list[ArtifactRecord]] = {}
        self._records: list[ArtifactRecord] = []
        self._merged_values: dict[tuple[str, str], Any] = {}
        self._last_writer: dict[tuple[str, str], str] = {}

    def publish_from_output(
        self,
        *,
        node_id: str,
        output: Any,
        ownership: tuple[str, ...] = (),
    ) -> list[ArtifactRecord]:
        """Parse node output and publish artifacts to the bus."""
        payload = self._extract_payload(
            node_id=node_id,
            output=output,
            ownership=ownership,
        )
        return self.publish(
            node_id=node_id,
            payload=payload,
            default_ownership=ownership,
        )

    def publish(
        self,
        *,
        node_id: str,
        payload: Any,
        default_ownership: tuple[str, ...] = (),
    ) -> list[ArtifactRecord]:
        """Validate and merge a producer payload."""
        artifacts_payload = _extract_artifact_list(payload)
        records = [
            ArtifactRecord.from_dict(
                item,
                node_id=node_id,
                index=index,
                default_ownership=default_ownership,
            )
            for index, item in enumerate(artifacts_payload)
        ]
        for record in records:
            self._merge_record(record)
            self._records.append(record)
            self._records_by_node.setdefault(record.node_id, []).append(record)
        return records

    def build_dependency_view(self, node_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        """Build consumer payload for dependency nodes."""
        view: dict[str, dict[str, Any]] = {}
        for node_id in node_ids:
            view[node_id] = self.build_node_bundle(node_id)
        return view

    def build_node_bundle(self, node_id: str) -> dict[str, Any]:
        """Build per-node artifact bundle for workflow summary/output."""
        records = list(self._records_by_node.get(node_id, []))
        merged: dict[str, Any] = {}
        for record in records:
            key_tuple = (record.artifact_type.value, record.key)
            merged_key = f"{record.artifact_type.value}:{record.key}"
            merged[merged_key] = self._merged_values.get(key_tuple, record.content)
        return {
            "artifacts": [record.to_dict() for record in records],
            "merged": merged,
        }

    def snapshot(self) -> dict[str, Any]:
        """Return global artifact bus snapshot."""
        merged: dict[str, Any] = {
            f"{artifact_type}:{key}": value
            for (artifact_type, key), value in self._merged_values.items()
        }
        return {
            "records": [record.to_dict() for record in self._records],
            "merged": merged,
        }

    def _merge_record(self, record: ArtifactRecord) -> None:
        key = (record.artifact_type.value, record.key)
        if key not in self._merged_values:
            self._merged_values[key] = record.content
            self._last_writer[key] = record.node_id
            return

        strategy = record.merge_strategy
        existing_value = self._merged_values[key]
        existing_node = self._last_writer.get(key, "<unknown>")

        if strategy == ArtifactMergeStrategy.REPLACE:
            self._merged_values[key] = record.content
            self._last_writer[key] = record.node_id
            return

        if strategy == ArtifactMergeStrategy.APPEND:
            if isinstance(existing_value, list):
                merged_value = list(existing_value)
            else:
                merged_value = [existing_value]
            merged_value.append(record.content)
            self._merged_values[key] = merged_value
            self._last_writer[key] = record.node_id
            return

        raise ArtifactConflictError(
            "artifact conflict for "
            f"{record.artifact_type.value}:{record.key} "
            f"(existing_node={existing_node}, incoming_node={record.node_id}, strategy=fail)"
        )

    def _extract_payload(
        self,
        *,
        node_id: str,
        output: Any,
        ownership: tuple[str, ...],
    ) -> Any:
        if isinstance(output, dict) and "artifacts" in output:
            return output
        if isinstance(output, list):
            return {"artifacts": output}
        if isinstance(output, dict) and "type" in output and "key" in output:
            return {"artifacts": [output]}
        if isinstance(output, str):
            stripped = output.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    decoded = json.loads(stripped)
                    if isinstance(decoded, dict) and "artifacts" in decoded:
                        return decoded
                    if isinstance(decoded, list):
                        return {"artifacts": decoded}
                    if isinstance(decoded, dict) and "type" in decoded and "key" in decoded:
                        return {"artifacts": [decoded]}
                except Exception:
                    pass
        return {
            "artifacts": [
                {
                    "type": ArtifactType.REPORT.value,
                    "key": f"{node_id}.report",
                    "content": "" if output is None else str(output),
                    "merge": ArtifactMergeStrategy.REPLACE.value,
                    "ownership": list(ownership),
                }
            ]
        }


def _extract_artifact_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise ArtifactSchemaError("artifact payload must contain artifacts as array")
        return artifacts
    if isinstance(payload, list):
        return payload
    raise ArtifactSchemaError("artifact payload must be an object or list")


def _coerce_string_tuple(raw: Any, *, field_name: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        value = raw.strip()
        return (value,) if value else ()
    if isinstance(raw, tuple):
        values = [str(item).strip() for item in raw if str(item).strip()]
        return tuple(values)
    if isinstance(raw, list):
        values = [str(item).strip() for item in raw if str(item).strip()]
        return tuple(values)
    raise ArtifactSchemaError(f"{field_name} must be a string or list of strings")


__all__ = [
    "ArtifactSchemaError",
    "ArtifactConflictError",
    "ArtifactType",
    "ArtifactMergeStrategy",
    "ArtifactRecord",
    "ArtifactBus",
]
