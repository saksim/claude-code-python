"""Runtime tests for P2-05 org policy + approval + audit workflow."""

from __future__ import annotations

import pytest

from claude_code.services.org_policy_audit import (
    OrgPolicyAuditError,
    OrgPolicyAuditService,
)


def test_policy_matcher_and_redaction_rules():
    service = OrgPolicyAuditService()
    service.configure_policies(
        policies=[
            {
                "id": "deny-bash-prod",
                "effect": "deny",
                "tool_pattern": "bash",
                "operation_pattern": "prod:*",
                "priority": 10,
                "reason": "production shell is blocked",
            },
            {
                "id": "allow-read",
                "effect": "allow",
                "tool_pattern": "read",
                "operation_pattern": "*",
                "priority": 20,
            },
        ]
    )

    denied = service.evaluate(
        tool_name="bash",
        operation="prod:deploy",
        payload={"token": "sk-very-secret-value"},
        actor="ops-bot",
    )
    assert denied["allowed"] is False
    assert denied["decision"] == "denied"
    assert denied["rule"]["id"] == "deny-bash-prod"
    assert denied["payload_redacted"]["token"] == "***REDACTED***"

    allowed = service.evaluate(
        tool_name="read",
        operation="repo:file",
        payload={"path": "README.md"},
        actor="dev-bot",
    )
    assert allowed["allowed"] is True
    assert allowed["decision"] == "allowed"
    assert allowed["rule"]["id"] == "allow-read"


def test_approval_state_transitions():
    service = OrgPolicyAuditService()
    service.configure_policies(
        policies=[
            {
                "id": "approve-write",
                "effect": "require_approval",
                "tool_pattern": "write",
                "operation_pattern": "*",
                "priority": 10,
            }
        ]
    )

    first = service.evaluate(
        tool_name="write",
        operation="repo:edit",
        payload={"content": "hello", "api_key": "abc"},
        actor="dev-bot",
    )
    assert first["allowed"] is False
    assert first["decision"] == "approval_pending"
    approval_id = first["approval"]["approval_id"]

    approvals = service.list_approvals(status="pending", limit=10)
    assert len(approvals) == 1
    assert approvals[0]["approval_id"] == approval_id

    decided = service.decide_approval(
        approval_id=approval_id,
        decision="approve",
        decided_by="sec-admin",
        reason="risk accepted",
    )
    assert decided["status"] == "approved"
    assert decided["decided_by"] == "sec-admin"

    allowed_after = service.evaluate(
        tool_name="write",
        operation="repo:edit",
        payload={"content": "hello", "api_key": "abc"},
        actor="dev-bot",
    )
    assert allowed_after["allowed"] is True
    assert allowed_after["decision"] == "allowed_by_approval"

    with pytest.raises(OrgPolicyAuditError) as exc_info:
        service.decide_approval(
            approval_id=approval_id,
            decision="reject",
            decided_by="sec-admin",
        )
    assert exc_info.value.code == "invalid_approval_transition"


def test_audit_chain_and_report_summary():
    service = OrgPolicyAuditService()
    service.configure_policies(
        policies=[
            {
                "id": "approve-agent",
                "effect": "require_approval",
                "tool_pattern": "agent",
                "operation_pattern": "*",
                "priority": 5,
            },
            {
                "id": "deny-rm",
                "effect": "deny",
                "tool_pattern": "bash",
                "operation_pattern": "danger:*",
                "priority": 10,
            },
        ]
    )

    pending = service.evaluate(
        tool_name="agent",
        operation="spawn",
        payload={"prompt": "run", "password": "p@ss"},
    )
    approval_id = pending["approval"]["approval_id"]

    service.decide_approval(
        approval_id=approval_id,
        decision="reject",
        decided_by="sec-admin",
        reason="missing ticket",
    )
    denied_by_approval = service.evaluate(
        tool_name="agent",
        operation="spawn",
        payload={"prompt": "run", "password": "p@ss"},
    )
    assert denied_by_approval["decision"] == "denied_by_approval"

    denied_direct = service.evaluate(
        tool_name="bash",
        operation="danger:rm-rf",
        payload={"command": "rm -rf /"},
    )
    assert denied_direct["decision"] == "denied"

    report = service.build_report(limit=200)
    assert report["summary"]["rule_count"] == 2
    assert report["summary"]["approval_total"] >= 1
    assert report["summary"]["audit_total"] >= 4
    assert report["decision_counts"].get("denied", 0) >= 1
    assert report["decision_counts"].get("denied_by_approval", 0) >= 1

    events = service.list_audit_events(event_type="org_policy.evaluated", limit=100)
    assert events
    assert all(event["event_type"] == "org_policy.evaluated" for event in events)


def test_policy_conflict_is_rejected():
    service = OrgPolicyAuditService()
    service.configure_policies(
        policies=[
            {
                "id": "allow-write-a",
                "effect": "allow",
                "tool_pattern": "write",
                "operation_pattern": "*",
                "priority": 10,
            },
            {
                "id": "deny-write-b",
                "effect": "deny",
                "tool_pattern": "write",
                "operation_pattern": "*",
                "priority": 10,
            },
        ]
    )

    with pytest.raises(OrgPolicyAuditError) as exc_info:
        service.evaluate(
            tool_name="write",
            operation="repo:edit",
            payload={"text": "x"},
        )
    assert exc_info.value.code == "policy_conflict"
    assert exc_info.value.status_code == 409
