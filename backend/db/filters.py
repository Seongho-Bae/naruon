from db.models import Email

def email_owner_filters(user_id: str, organization_id: str | None):
    organization_filter = (
        Email.organization_id == organization_id
        if organization_id is not None
        else Email.organization_id.is_(None)
    )
    return (Email.user_id == user_id, organization_filter)
