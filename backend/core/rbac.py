import enum
from typing import Dict, Any
from pydantic import BaseModel
from api.auth import RoleName


class ResourceAction(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class AbacPolicy(BaseModel):
    policy_id: str
    resource_type: str
    action: ResourceAction
    conditions: Dict[str, Any]  # e.g. {"department": "sales", "clearance": "high"}


def check_tenant_access(user_role: RoleName, required_role: RoleName) -> bool:
    """
    Check if the user's role satisfies the required role.
    Higher privileges include lower privileges.
    Universal mapping:
    - platform_admin: SaaS Provider / System Admin
    - organization_admin: Corporate Admin / Tenant Owner
    - group_admin: IT Operator / Department Head
    - member: B2B2C User or B2C Individual
    """
    hierarchy = {
        "member": 0,
        "group_admin": 1,
        "organization_admin": 2,
        "platform_admin": 3,
    }

    if user_role not in hierarchy or required_role not in hierarchy:
        return False

    return hierarchy[user_role] >= hierarchy[required_role]


def evaluate_abac_policy(user_attributes: Dict[str, Any], policy: AbacPolicy) -> bool:
    """
    Evaluate Attribute-Based Access Control policies.
    """
    for key, expected_value in policy.conditions.items():
        if user_attributes.get(key) != expected_value:
            return False
    return True
