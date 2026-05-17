from services.access_policy import AccessRequest, ResourcePolicy, evaluate_access


def test_abac_organization_denial_precedes_role_and_group_allow():
    decision = evaluate_access(
        AccessRequest(
            user_id="alice",
            role="organization_admin",
            organization_id="org-other",
            group_ids=("exec",),
            data_region="eu",
            consent_scopes=("mail.read",),
        ),
        ResourcePolicy(
            owner_id="alice",
            organization_id="org-acme",
            permitted_roles=("organization_admin",),
            permitted_group_ids=("exec",),
            data_region="eu",
            required_consent_scopes=("mail.read",),
        ),
    )

    assert decision.allowed is False
    assert decision.reason == "organization_denied"


def test_abac_data_region_denial_overrides_platform_admin_rbac_allow():
    decision = evaluate_access(
        AccessRequest(
            user_id="root",
            role="platform_admin",
            organization_id="org-acme",
            group_ids=("exec",),
            data_region="us",
            consent_scopes=("mail.read",),
        ),
        ResourcePolicy(
            owner_id="alice",
            organization_id="org-acme",
            permitted_roles=("platform_admin",),
            permitted_group_ids=("exec",),
            data_region="eu",
            required_consent_scopes=("mail.read",),
        ),
    )

    assert decision.allowed is False
    assert decision.reason == "data_region_denied"


def test_abac_owner_denial_overrides_group_admin_rbac_allow_without_delegation():
    decision = evaluate_access(
        AccessRequest(
            user_id="bob",
            role="group_admin",
            organization_id="org-acme",
            group_ids=("sales",),
            data_region="eu",
            consent_scopes=("mail.read",),
        ),
        ResourcePolicy(
            owner_id="alice",
            organization_id="org-acme",
            permitted_roles=("group_admin",),
            permitted_group_ids=("sales",),
            data_region="eu",
            required_consent_scopes=("mail.read",),
        ),
    )

    assert decision.allowed is False
    assert decision.reason == "ownership_denied"


def test_abac_consent_denial_overrides_member_rbac_allow():
    decision = evaluate_access(
        AccessRequest(
            user_id="alice",
            role="member",
            organization_id="org-acme",
            group_ids=(),
            data_region="eu",
            consent_scopes=("calendar.read",),
        ),
        ResourcePolicy(
            owner_id="alice",
            organization_id="org-acme",
            permitted_roles=("member",),
            permitted_group_ids=(),
            data_region="eu",
            required_consent_scopes=("mail.read",),
        ),
    )

    assert decision.allowed is False
    assert decision.reason == "consent_denied"


def test_abac_delegation_allows_non_owner_after_all_denials_clear():
    decision = evaluate_access(
        AccessRequest(
            user_id="delegate",
            role="member",
            organization_id="org-acme",
            group_ids=("assistants",),
            data_region="eu",
            consent_scopes=("mail.read",),
        ),
        ResourcePolicy(
            owner_id="alice",
            organization_id="org-acme",
            permitted_roles=("member",),
            permitted_group_ids=("assistants",),
            data_region="eu",
            required_consent_scopes=("mail.read",),
            delegated_user_ids=("delegate",),
        ),
    )

    assert decision.allowed is True
    assert decision.reason == "allowed"
