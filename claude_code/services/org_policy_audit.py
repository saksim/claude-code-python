"""Organization policy + audit service for workflow card P2-05."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class OrgPolicyAuditError(RuntimeError):
    """Raised when org policy/audit workflow fails with structured metadata."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "org_policy_audit_error",
        status_code: int = 500,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class PolicyEffect(Enum):
    """Supported policy effects."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class ApprovalStatus(Enum):
    """Lifecycle for approval queue items."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class OrgPolicyRule:
    """One org-level policy rule."""

    rule_id: str
    effect: PolicyEffect
    tool_pattern: str = "*"
    operation_pattern: str = "*"
    priority: int = 100
    enabled: bool = True
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, index: int) -> "OrgPolicyRule":
        """Build validated rule from request payload."""
        if not isinstance(payload, dict):
            raise OrgPolicyAuditError(
                f"policies[{index}] must be an object",
                code="validation_error",
                status_code=400,
            )

        effect_raw = str(payload.get("effect") or "").strip().lower()
        try:
            effect = PolicyEffect(effect_raw)
        except ValueError as exc:
            supported = ", ".join(item.value for item in PolicyEffect)
            raise OrgPolicyAuditError(
                f"policies[{index}].effect must be one of: {supported}",
                code="validation_error",
                status_code=400,
            ) from exc

        priority_raw = payload.get("priority", 100)
        try:
            priority = int(priority_raw)
        except Exception as exc:
            raise OrgPolicyAuditError(
                f"policies[{index}].priority must be an integer",
                code="validation_error",
                status_code=400,
            ) from exc

        metadata_raw = payload.get("metadata", {})
        if metadata_raw is None:
            metadata = {}
        elif isinstance(metadata_raw, dict):
            metadata = dict(metadata_raw)
        else:
            raise OrgPolicyAuditError(
                f"policies[{index}].metadata must be an object",
                code="validation_error",
                status_code=400,
            )

        rule_id = str(payload.get("id") or f"policy-{index}")
        return cls(
            rule_id=rule_id,
            effect=effect,
            tool_pattern=str(payload.get("tool_pattern") or payload.get("tool") or "*"),
            operation_pattern=str(payload.get("operation_pattern") or payload.get("operation") or "*"),
            priority=priority,
            enabled=bool(payload.get("enabled", True)),
            reason=str(payload.get("reason") or ""),
            metadata=metadata,
        )

    def matches(self, *, tool_name: str, operation: str) -> bool:
        """Return whether this rule applies to the request."""
        if not self.enabled:
            return False
        return fnmatch.fnmatch(tool_name, self.tool_pattern) and fnmatch.fnmatch(
            operation,
            self.operation_pattern,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule for API response."""
        return {
            "id": self.rule_id,
            "effect": self.effect.value,
            "tool_pattern": self.tool_pattern,
            "operation_pattern": self.operation_pattern,
            "priority": self.priority,
            "enabled": self.enabled,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ApprovalRequest:
    """Approval queue item."""

    approval_id: str
    rule_id: str
    tool_name: str
    operation: str
    payload_hash: str
    payload_redacted: Any
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    decided_by: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize approval request."""
        return {
            "approval_id": self.approval_id,
            "rule_id": self.rule_id,
            "tool_name": self.tool_name,
            "operation": self.operation,
            "payload_hash": self.payload_hash,
            "payload_redacted": self.payload_redacted,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "decided_by": self.decided_by,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Policy audit record."""

    event_id: str
    event_type: str
    created_at: float
    tool_name: str | None
    operation: str | None
    decision: str | None
    rule_id: str | None
    approval_id: str | None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize audit event."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "tool_name": self.tool_name,
            "operation": self.operation,
            "decision": self.decision,
            "rule_id": self.rule_id,
            "approval_id": self.approval_id,
            "details": dict(self.details),
        }


_SENSITIVE_TOKENS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
)

_SENSITIVE_PREFIXES: tuple[str, ...] = (
    "sk-",
    "ghp_",
    "github_pat_",
    "xoxb-",
    "xoxp-",
)


class OrgPolicyAuditService:
    """P2-05 runtime service: policy matcher + approval queue + audit reporting."""

    def __init__(
        self,
        *,
        append_event: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._rules: list[OrgPolicyRule] = []
        self._approvals: dict[str, ApprovalRequest] = {}
        self._approvals_by_fingerprint: dict[str, str] = {}
        self._audit_events: list[AuditEvent] = []
        self._append_event = append_event
        self._approval_counter = 0
        self._audit_counter = 0

    def configure_policies(
        self,
        *,
        policies: list[dict[str, Any]],
        replace: bool = True,
    ) -> dict[str, Any]:
        """Register policy set for org-level execution control."""
        parsed = [
            OrgPolicyRule.from_dict(item, index=index)
            for index, item in enumerate(policies)
        ]

        if replace:
            self._rules = parsed
        else:
            self._rules.extend(parsed)

        self._write_audit(
            event_type="org_policy.rules.configured",
            details={
                "replace": replace,
                "rule_count": len(self._rules),
            },
        )
        return {
            "rule_count": len(self._rules),
            "rules": [rule.to_dict() for rule in self._rules],
        }

    def evaluate(
        self,
        *,
        tool_name: str,
        operation: str = "execute",
        payload: Any = None,
        actor: str | None = None,
        context: Optional[dict[str, Any]] = None,
        create_approval: bool = True,
    ) -> dict[str, Any]:
        """Evaluate one execution request against org policy."""
        if not tool_name.strip():
            raise OrgPolicyAuditError(
                "tool_name is required",
                code="validation_error",
                status_code=400,
            )

        clean_tool_name = tool_name.strip()
        clean_operation = operation.strip() or "execute"
        payload_redacted = self.redact_secrets(payload)
        payload_hash = _stable_hash(payload)

        matched = [
            rule
            for rule in self._rules
            if rule.matches(tool_name=clean_tool_name, operation=clean_operation)
        ]
        matched.sort(key=lambda item: (item.priority, item.rule_id))

        rule, conflict = self._select_effective_rule(matched)
        if conflict is not None:
            self._write_audit(
                event_type="org_policy.conflict.detected",
                tool_name=clean_tool_name,
                operation=clean_operation,
                decision="blocked",
                rule_id=None,
                details=conflict,
            )
            raise OrgPolicyAuditError(
                "conflicting policies detected at same priority",
                code="policy_conflict",
                status_code=409,
                details=conflict,
            )

        approval = None
        decision = "allowed"
        allowed = True

        if rule.effect == PolicyEffect.DENY:
            decision = "denied"
            allowed = False
        elif rule.effect == PolicyEffect.REQUIRE_APPROVAL:
            fingerprint = self._approval_fingerprint(
                rule_id=rule.rule_id,
                tool_name=clean_tool_name,
                operation=clean_operation,
                payload_hash=payload_hash,
            )
            approval = self._get_approval_by_fingerprint(fingerprint)
            if approval is None and create_approval:
                approval = self._create_approval(
                    rule_id=rule.rule_id,
                    tool_name=clean_tool_name,
                    operation=clean_operation,
                    payload_hash=payload_hash,
                    payload_redacted=payload_redacted,
                    fingerprint=fingerprint,
                )
                decision = "approval_pending"
                allowed = False
            elif approval is None:
                decision = "approval_required"
                allowed = False
            elif approval.status == ApprovalStatus.APPROVED:
                decision = "allowed_by_approval"
                allowed = True
            elif approval.status in (ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED):
                decision = "denied_by_approval"
                allowed = False
            else:
                decision = "approval_pending"
                allowed = False

        details = {
            "actor": actor,
            "context": dict(context or {}),
            "payload_redacted": payload_redacted,
            "matched_rule_count": len(matched),
        }
        audit = self._write_audit(
            event_type="org_policy.evaluated",
            tool_name=clean_tool_name,
            operation=clean_operation,
            decision=decision,
            rule_id=rule.rule_id,
            approval_id=approval.approval_id if approval else None,
            details=details,
        )

        result = {
            "allowed": allowed,
            "decision": decision,
            "tool_name": clean_tool_name,
            "operation": clean_operation,
            "rule": rule.to_dict(),
            "payload_redacted": payload_redacted,
            "audit_event_id": audit.event_id,
        }
        if approval is not None:
            result["approval"] = approval.to_dict()
        return result

    def decide_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        decided_by: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Apply transition to approval queue item."""
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise OrgPolicyAuditError(
                f"approval not found: {approval_id}",
                code="approval_not_found",
                status_code=404,
            )

        decision_normalized = decision.strip().lower()
        if decision_normalized not in {"approve", "reject", "cancel"}:
            raise OrgPolicyAuditError(
                f"unsupported approval decision: {decision}",
                code="validation_error",
                status_code=400,
            )

        if approval.status != ApprovalStatus.PENDING:
            raise OrgPolicyAuditError(
                f"approval transition is not allowed from {approval.status.value}",
                code="invalid_approval_transition",
                status_code=409,
                details={
                    "approval_id": approval.approval_id,
                    "status": approval.status.value,
                },
            )

        if decision_normalized == "approve":
            new_status = ApprovalStatus.APPROVED
        elif decision_normalized == "reject":
            new_status = ApprovalStatus.REJECTED
        else:
            new_status = ApprovalStatus.CANCELLED

        approval.status = new_status
        approval.decided_by = decided_by
        approval.reason = reason
        approval.updated_at = time.time()

        self._write_audit(
            event_type="org_policy.approval.decided",
            tool_name=approval.tool_name,
            operation=approval.operation,
            decision=new_status.value,
            rule_id=approval.rule_id,
            approval_id=approval.approval_id,
            details={
                "decided_by": decided_by,
                "reason": reason,
            },
        )
        return approval.to_dict()

    def list_approvals(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List approval queue with optional status filter."""
        approvals = list(self._approvals.values())
        if status:
            normalized = status.strip().lower()
            approvals = [item for item in approvals if item.status.value == normalized]
        approvals.sort(key=lambda item: item.created_at, reverse=True)
        return [item.to_dict() for item in approvals[:limit]]

    def list_audit_events(
        self,
        *,
        event_type: str | None = None,
        tool_name: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List audit events with basic filters."""
        events = list(self._audit_events)
        if event_type:
            normalized = event_type.strip()
            events = [item for item in events if item.event_type == normalized]
        if tool_name:
            normalized_tool = tool_name.strip()
            events = [item for item in events if item.tool_name == normalized_tool]
        events.sort(key=lambda item: item.created_at, reverse=True)
        return [item.to_dict() for item in events[:limit]]

    def build_report(self, *, limit: int = 200) -> dict[str, Any]:
        """Build compact audit summary for org reporting."""
        latest = self.list_audit_events(limit=limit)
        decision_count: dict[str, int] = {}
        for item in latest:
            decision = str(item.get("decision") or "none")
            decision_count[decision] = decision_count.get(decision, 0) + 1
        pending = len([item for item in self._approvals.values() if item.status == ApprovalStatus.PENDING])
        return {
            "summary": {
                "rule_count": len(self._rules),
                "approval_total": len(self._approvals),
                "approval_pending": pending,
                "audit_total": len(self._audit_events),
            },
            "decision_counts": decision_count,
            "events": latest,
        }

    def redact_secrets(self, value: Any) -> Any:
        """Redact sensitive fields recursively."""
        return _redact_value(value)

    def _select_effective_rule(
        self,
        matched_rules: list[OrgPolicyRule],
    ) -> tuple[OrgPolicyRule, dict[str, Any] | None]:
        if not matched_rules:
            return (
                OrgPolicyRule(
                    rule_id="__default_allow__",
                    effect=PolicyEffect.ALLOW,
                    tool_pattern="*",
                    operation_pattern="*",
                    priority=99999,
                    enabled=True,
                    reason="no policy matched",
                ),
                None,
            )

        top_priority = matched_rules[0].priority
        top_rules = [item for item in matched_rules if item.priority == top_priority]
        effects = sorted({item.effect.value for item in top_rules})
        if len(effects) <= 1:
            return top_rules[0], None

        return (
            top_rules[0],
            {
                "priority": top_priority,
                "rules": [item.to_dict() for item in top_rules],
                "effects": effects,
            },
        )

    def _create_approval(
        self,
        *,
        rule_id: str,
        tool_name: str,
        operation: str,
        payload_hash: str,
        payload_redacted: Any,
        fingerprint: str,
    ) -> ApprovalRequest:
        self._approval_counter += 1
        approval_id = f"apr-{int(time.time() * 1000)}-{self._approval_counter}"
        approval = ApprovalRequest(
            approval_id=approval_id,
            rule_id=rule_id,
            tool_name=tool_name,
            operation=operation,
            payload_hash=payload_hash,
            payload_redacted=payload_redacted,
        )
        self._approvals[approval_id] = approval
        self._approvals_by_fingerprint[fingerprint] = approval_id

        self._write_audit(
            event_type="org_policy.approval.created",
            tool_name=tool_name,
            operation=operation,
            decision=ApprovalStatus.PENDING.value,
            rule_id=rule_id,
            approval_id=approval_id,
            details={"payload_redacted": payload_redacted},
        )
        return approval

    def _approval_fingerprint(
        self,
        *,
        rule_id: str,
        tool_name: str,
        operation: str,
        payload_hash: str,
    ) -> str:
        return "|".join([rule_id, tool_name, operation, payload_hash])

    def _get_approval_by_fingerprint(self, fingerprint: str) -> ApprovalRequest | None:
        approval_id = self._approvals_by_fingerprint.get(fingerprint)
        if approval_id is None:
            return None
        return self._approvals.get(approval_id)

    def _write_audit(
        self,
        *,
        event_type: str,
        tool_name: str | None = None,
        operation: str | None = None,
        decision: str | None = None,
        rule_id: str | None = None,
        approval_id: str | None = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        self._audit_counter += 1
        event = AuditEvent(
            event_id=f"audit-{int(time.time() * 1000)}-{self._audit_counter}",
            event_type=event_type,
            created_at=time.time(),
            tool_name=tool_name,
            operation=operation,
            decision=decision,
            rule_id=rule_id,
            approval_id=approval_id,
            details=dict(details or {}),
        )
        self._audit_events.append(event)
        append_event = self._append_event
        if callable(append_event):
            try:
                append_event(
                    event_type=event.event_type,
                    payload={
                        "tool_name": event.tool_name,
                        "operation": event.operation,
                        "decision": event.decision,
                        "rule_id": event.rule_id,
                        "approval_id": event.approval_id,
                        "details": event.details,
                    },
                    source="org_policy_audit_service",
                )
            except Exception:
                pass
        return event


def _stable_hash(payload: Any) -> str:
    try:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    except TypeError:
        encoded = str(payload)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for raw_key, raw_item in value.items():
            key = str(raw_key)
            if _is_sensitive_key(key):
                redacted[key] = "***REDACTED***"
                continue
            redacted[key] = _redact_value(raw_item)
        return redacted

    if isinstance(value, list):
        return [_redact_value(item) for item in value]

    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]

    if isinstance(value, str) and _looks_like_secret(value):
        return "***REDACTED***"

    return value


def _is_sensitive_key(key: str) -> bool:
    lowered = key.strip().lower()
    if not lowered:
        return False
    return any(token in lowered for token in _SENSITIVE_TOKENS)


def _looks_like_secret(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    lowered = text.lower()
    if any(lowered.startswith(prefix) for prefix in _SENSITIVE_PREFIXES):
        return True
    if len(text) >= 40 and any(ch.isdigit() for ch in text) and any(ch.isalpha() for ch in text):
        return True
    return False


__all__ = [
    "OrgPolicyAuditError",
    "PolicyEffect",
    "ApprovalStatus",
    "OrgPolicyRule",
    "ApprovalRequest",
    "AuditEvent",
    "OrgPolicyAuditService",
]
