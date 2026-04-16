"""Tests for unified permission checker semantics."""

from __future__ import annotations

from claude_code.permissions import create_permission_checker


def test_plan_mode_allows_read_only_tools():
    checker = create_permission_checker(mode="plan")
    assert checker.can_execute("read") is True
    assert checker.can_execute("glob") is True
    assert checker.can_execute("write") is False
    assert checker.can_execute("bash") is False


def test_accept_edits_mode_allows_file_edits():
    checker = create_permission_checker(mode="acceptEdits")
    assert checker.can_execute("read") is True
    assert checker.can_execute("write") is True
    assert checker.can_execute("edit") is True
    assert checker.can_execute("bash") is False


def test_strict_mode_has_defined_rules():
    checker = create_permission_checker(mode="strict")
    assert checker.can_execute("read") is True
    assert checker.can_execute("bash") is False


def test_rule_prefix_parsing_supports_wildcard_suffix():
    checker = create_permission_checker(
        mode="default",
        always_allow=["task_*"],
        always_deny=["task_kill"],
    )
    assert checker.can_execute("task_list") is True
    assert checker.can_execute("task_kill") is False

