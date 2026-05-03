"""Phase 2 card P2-16 gate for Linux CI matrix generation.

This script converts shard plan artifacts from P2-15 into a CI-consumable
matrix payload for fan-out jobs and optional GitHub Actions outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coerce_int(value: Any, *, field: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{path}: field '{field}' must be int")
    return value


def _coerce_str(value: Any, *, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path}: field '{field}' must be non-empty string")
    return value


def _coerce_str_list(value: Any, *, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{path}: field '{field}' must be string list")
    return list(value)


def load_shard_plan(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{path}: shard plan file not found")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: shard plan payload must be object")

    required_fields = ("manifest_total_tests", "shard_total", "shards")
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{path}: missing field '{field}'")

    manifest_total_tests = _coerce_int(
        payload["manifest_total_tests"],
        field="manifest_total_tests",
        path=path,
    )
    shard_total = _coerce_int(payload["shard_total"], field="shard_total", path=path)
    shards = payload["shards"]
    if not isinstance(shards, list):
        raise ValueError(f"{path}: field 'shards' must be list")

    if manifest_total_tests < 0:
        raise ValueError(f"{path}: manifest_total_tests must be >= 0")
    if shard_total < 1:
        raise ValueError(f"{path}: shard_total must be >= 1")

    normalized_shards: list[dict[str, Any]] = []
    seen_indexes: set[int] = set()
    for index, shard in enumerate(shards, start=1):
        if not isinstance(shard, dict):
            raise ValueError(f"{path}: shards[{index - 1}] must be object")

        for required in ("shard_index", "total_tests", "report_dir", "summary_path", "command", "command_parts"):
            if required not in shard:
                raise ValueError(f"{path}: shards[{index - 1}] missing field '{required}'")

        shard_index = _coerce_int(
            shard["shard_index"],
            field=f"shards[{index - 1}].shard_index",
            path=path,
        )
        total_tests = _coerce_int(
            shard["total_tests"],
            field=f"shards[{index - 1}].total_tests",
            path=path,
        )
        report_dir = _coerce_str(
            shard["report_dir"],
            field=f"shards[{index - 1}].report_dir",
            path=path,
        )
        summary_path = _coerce_str(
            shard["summary_path"],
            field=f"shards[{index - 1}].summary_path",
            path=path,
        )
        command = _coerce_str(
            shard["command"],
            field=f"shards[{index - 1}].command",
            path=path,
        )
        command_parts = _coerce_str_list(
            shard["command_parts"],
            field=f"shards[{index - 1}].command_parts",
            path=path,
        )
        test_files = shard.get("test_files", [])
        if not isinstance(test_files, list) or not all(isinstance(item, str) for item in test_files):
            raise ValueError(f"{path}: field 'shards[{index - 1}].test_files' must be string list")

        nested_shard_total = shard.get("shard_total", shard_total)
        if nested_shard_total != shard_total:
            raise ValueError(
                f"{path}: shards[{index - 1}].shard_total ({nested_shard_total}) "
                f"!= top-level shard_total ({shard_total})"
            )
        if shard_index < 1 or shard_index > shard_total:
            raise ValueError(f"{path}: shards[{index - 1}].shard_index out of range")
        if shard_index in seen_indexes:
            raise ValueError(f"{path}: duplicate shard_index {shard_index}")
        if total_tests < 0:
            raise ValueError(f"{path}: shards[{index - 1}].total_tests must be >= 0")

        seen_indexes.add(shard_index)
        normalized_shards.append(
            {
                "shard_index": shard_index,
                "shard_total": shard_total,
                "total_tests": total_tests,
                "test_files": list(test_files),
                "report_dir": report_dir,
                "summary_path": summary_path,
                "command": command,
                "command_parts": command_parts,
            }
        )

    expected_indexes = set(range(1, shard_total + 1))
    if seen_indexes != expected_indexes:
        missing = sorted(expected_indexes - seen_indexes)
        extra = sorted(seen_indexes - expected_indexes)
        raise ValueError(
            f"{path}: shard indexes mismatch (missing={missing}, unexpected={extra})"
        )

    total_tests = sum(int(item["total_tests"]) for item in normalized_shards)
    if total_tests != manifest_total_tests:
        raise ValueError(
            f"{path}: shard total_tests sum ({total_tests}) "
            f"!= manifest_total_tests ({manifest_total_tests})"
        )

    return {
        "manifest_total_tests": manifest_total_tests,
        "shard_total": shard_total,
        "shards": sorted(normalized_shards, key=lambda item: int(item["shard_index"])),
    }


def build_ci_matrix_payload(
    shard_plan: dict[str, Any],
    *,
    source_path: Path,
    skip_empty_shards: bool,
) -> dict[str, Any]:
    include: list[dict[str, Any]] = []
    summary_paths: list[str] = []
    for shard in shard_plan["shards"]:
        total_tests = int(shard["total_tests"])
        if skip_empty_shards and total_tests == 0:
            continue
        include_entry = {
            "shard_index": int(shard["shard_index"]),
            "shard_total": int(shard["shard_total"]),
            "total_tests": total_tests,
            "report_dir": str(shard["report_dir"]),
            "summary_path": str(shard["summary_path"]),
            "command": str(shard["command"]),
            "command_parts": list(shard["command_parts"]),
        }
        include.append(include_entry)
        summary_paths.append(include_entry["summary_path"])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_shard_plan": str(source_path),
        "shard_total": int(shard_plan["shard_total"]),
        "manifest_total_tests": int(shard_plan["manifest_total_tests"]),
        "selected_shards": len(include),
        "skipped_empty_shards": bool(skip_empty_shards),
        "matrix": {"include": include},
        "summary_paths": summary_paths,
    }


def build_github_output_values(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "matrix": json.dumps(payload["matrix"], ensure_ascii=False, separators=(",", ":")),
        "summary_paths": json.dumps(payload["summary_paths"], ensure_ascii=False, separators=(",", ":")),
        "selected_shards": str(payload["selected_shards"]),
        "shard_total": str(payload["shard_total"]),
        "manifest_total_tests": str(payload["manifest_total_tests"]),
    }


def write_github_output(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Linux CI matrix from P2 shard plan"
    )
    parser.add_argument(
        "--shard-plan",
        default=".claude/reports/linux_unified_gate/shard_plan.json",
        help="Shard plan JSON produced by run_p2_linux_shard_plan_gate.py",
    )
    parser.add_argument(
        "--output",
        default=".claude/reports/linux_unified_gate/ci_matrix.json",
        help="Output CI matrix JSON path",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Optional GitHub Actions output file path (appends matrix/summary_paths fields)",
    )
    parser.add_argument(
        "--skip-empty-shards",
        action="store_true",
        help="Skip shards with zero assigned tests",
    )
    parser.add_argument(
        "--print-matrix",
        action="store_true",
        help="Print generated matrix payload JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and print summary without writing output file",
    )
    args = parser.parse_args()

    shard_plan_path = Path(args.shard_plan)
    try:
        shard_plan = load_shard_plan(shard_plan_path)
        payload = build_ci_matrix_payload(
            shard_plan,
            source_path=shard_plan_path.resolve(),
            skip_empty_shards=args.skip_empty_shards,
        )
    except ValueError as exc:
        print(f"[p2-linux-ci-matrix-gate] {exc}", file=sys.stderr)
        return 2

    if not args.dry_run:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"ci matrix: {output_path}")

    if args.github_output:
        write_github_output(Path(args.github_output), build_github_output_values(payload))
        print(f"github output: {args.github_output}")

    print(
        "matrix summary: "
        f"{payload['selected_shards']} shards selected "
        f"(manifest_total_tests={payload['manifest_total_tests']})"
    )
    if args.print_matrix or args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
