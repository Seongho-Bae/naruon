"""Pure RBAC/ABAC access policy decisions for workspace resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


PolicyRoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]
DecisionReason = Literal[
    "allowed",
    "organization_denied",
    "data_region_denied",
    "consent_denied",
    "ownership_denied",
    "rbac_denied",
]


@dataclass(frozen=True)
class AccessRequest:
    user_id: str
    role: PolicyRoleName
    organization_id: str | None
    group_ids: tuple[str, ...]
    data_region: str | None
    consent_scopes: tuple[str, ...]


@dataclass(frozen=True)
class ResourcePolicy:
    owner_id: str
    organization_id: str | None
    permitted_roles: tuple[PolicyRoleName, ...]
    permitted_group_ids: tuple[str, ...]
    data_region: str | None
    required_consent_scopes: tuple[str, ...]
    delegated_user_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: DecisionReason


def evaluate_access(request: AccessRequest, resource: ResourcePolicy) -> AccessDecision:
    """Evaluate resource access with ABAC denials before RBAC allows."""
    if request.organization_id != resource.organization_id:
        return AccessDecision(allowed=False, reason="organization_denied")

    if request.data_region != resource.data_region:
        return AccessDecision(allowed=False, reason="data_region_denied")

    missing_consent = set(resource.required_consent_scopes) - set(request.consent_scopes)
    if missing_consent:
        return AccessDecision(allowed=False, reason="consent_denied")

    owns_resource = request.user_id == resource.owner_id
    has_delegation = request.user_id in resource.delegated_user_ids
    if not owns_resource and not has_delegation:
        return AccessDecision(allowed=False, reason="ownership_denied")

    role_allowed = request.role in resource.permitted_roles
    group_allowed = bool(set(request.group_ids) & set(resource.permitted_group_ids))
    if not role_allowed and not group_allowed:
        return AccessDecision(allowed=False, reason="rbac_denied")

    return AccessDecision(allowed=True, reason="allowed")
