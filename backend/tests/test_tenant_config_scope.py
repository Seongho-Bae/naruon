from services.tenant_config_scope import tenant_config_owner_filters

def test_tenant_config_owner_filters_with_org():
    """Test generating filters when an organization_id is provided"""
    user_id = "user1"
    org_id = "org1"
    filters = tenant_config_owner_filters(user_id, org_id)

    assert len(filters) == 2
    user_filter, org_filter = filters

    # Verify user_filter: TenantConfig.user_id == user_id
    assert str(user_filter.left) == "tenant_configs.user_id"
    assert user_filter.right.value == user_id

    # Verify org_filter: TenantConfig.organization_id == org_id
    assert str(org_filter.left) == "tenant_configs.organization_id"
    assert org_filter.right.value == org_id

def test_tenant_config_owner_filters_without_org():
    """Test generating filters when organization_id is None"""
    user_id = "user1"
    filters = tenant_config_owner_filters(user_id, None)

    assert len(filters) == 2
    user_filter, org_filter = filters

    # Verify user_filter: TenantConfig.user_id == user_id
    assert str(user_filter.left) == "tenant_configs.user_id"
    assert user_filter.right.value == user_id

    # Verify org_filter: TenantConfig.organization_id.is_(None)
    assert str(org_filter.left) == "tenant_configs.organization_id"
    assert org_filter.operator.__name__ == "is_"
    # No right.value for IS NULL operator, so we check the operator name
