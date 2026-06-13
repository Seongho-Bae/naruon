import datetime
import logging
import uuid

from cryptography.fernet import Fernet, InvalidToken
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from core.config import settings
from core.runtime_secrets import EncryptionKeyRing, build_encryption_keyring

logger = logging.getLogger(__name__)

Base = declarative_base()

VERSIONED_FERNET_PREFIX = "fernet:v1:"


def get_encryption_keyring() -> EncryptionKeyRing:
    active_key = (
        settings.ENCRYPTION_KEY.get_secret_value()
        if settings.ENCRYPTION_KEY is not None
        else None
    )
    previous_keys = (
        settings.ENCRYPTION_PREVIOUS_KEYS.get_secret_value()
        if settings.ENCRYPTION_PREVIOUS_KEYS is not None
        else None
    )
    return build_encryption_keyring(
        active_key_value=active_key,
        active_key_id=settings.ENCRYPTION_KEY_ID,
        previous_keys_value=previous_keys,
    )


def get_fernet() -> Fernet:
    return get_encryption_keyring().active_key.fernet


def encrypt_sensitive_value(value: str) -> str:
    keyring = get_encryption_keyring()
    encrypted_value = keyring.active_key.fernet.encrypt(value.encode("utf-8")).decode(
        "utf-8"
    )
    return f"{VERSIONED_FERNET_PREFIX}{keyring.active_key.key_id}:{encrypted_value}"


def _parse_versioned_encrypted_value(value: str) -> tuple[str, str] | None:
    if not value.startswith(VERSIONED_FERNET_PREFIX):
        return None
    key_payload = value.removeprefix(VERSIONED_FERNET_PREFIX)
    key_id, separator, encrypted_value = key_payload.partition(":")
    if not separator or not key_id or not encrypted_value:
        raise InvalidToken
    return key_id, encrypted_value


def decrypt_sensitive_value(value: str) -> str:
    keyring = get_encryption_keyring()
    versioned_value = _parse_versioned_encrypted_value(value)
    if versioned_value is not None:
        key_id, encrypted_value = versioned_value
        encryption_key = keyring.key_for_id(key_id)
        if encryption_key is None:
            raise InvalidToken
        return encryption_key.fernet.decrypt(encrypted_value.encode("utf-8")).decode(
            "utf-8"
        )

    last_error: InvalidToken | None = None
    for encryption_key in keyring.all_keys():
        try:
            return encryption_key.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            last_error = exc
    raise last_error or InvalidToken


class EncryptedString(TypeDecorator):
    """
    Encrypts string values before saving to the database and decrypts them when
    retrieving.
    Uses Fernet symmetric encryption.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt_sensitive_value(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return decrypt_sensitive_value(value)
            except (InvalidToken, UnicodeDecodeError):
                logger.warning(
                    "Failed to decrypt field in EncryptedString; returning None"
                )
                return None
        return value


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    user_id: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String)
    resource_type: Mapped[str] = mapped_column(String)
    resource_id: Mapped[str | None] = mapped_column(String, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_events"

    event_uid: Mapped[str] = mapped_column(
        String, default=lambda: uuid.uuid4().hex, primary_key=True
    )
    actor_user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    actor_role: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    event_action: Mapped[str] = mapped_column(String, index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    resource_uid: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    evidence_source: Mapped[str] = mapped_column(String, nullable=False)
    detail_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True,
    )
    __table_args__ = (
        Index(
            "ix_security_audit_events_scope_time",
            "organization_id",
            "workspace_id",
            "observed_at",
        ),
        Index(
            "ix_security_audit_events_actor_scope",
            "actor_user_id",
            "organization_id",
            "workspace_id",
        ),
    )


class RevokedSessionToken(Base):
    __tablename__ = "revoked_session_tokens"

    token_fingerprint: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    revoked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index(
            "ix_revoked_session_tokens_scope_expiry",
            "organization_id",
            "workspace_id",
            "expires_at",
        ),
    )


class LLMProvider(Base):
    __tablename__ = "llm_providers"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_llm_providers_org_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, index=True)
    provider_type: Mapped[str] = mapped_column(
        String
    )  # e.g. openai, anthropic, gemini, ollama
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    api_key: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class WorkspaceRunnerConfig(Base):
    __tablename__ = "workspace_runner_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    workspace_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    registration_token: Mapped[str | None] = mapped_column(
        EncryptedString, nullable=True
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class ConnectorSignalEvent(Base):
    __tablename__ = "connector_signal_events"

    event_uid: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: f"connector_evt_{uuid.uuid4().hex}",
    )
    organization_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    signal_key: Mapped[str] = mapped_column(String, index=True, nullable=False)
    state_code: Mapped[str] = mapped_column(String, index=True, nullable=False)
    detail_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    __table_args__ = (
        Index(
            "ix_connector_signal_events_scope_time",
            "organization_id",
            "workspace_id",
            "observed_at",
        ),
    )


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    groups: Mapped[list["OrganizationGroup"]] = relationship(
        back_populates="organization"
    )
    role_assignments: Mapped[list["ScopedRoleAssignment"]] = relationship(
        back_populates="organization"
    )


class OrganizationGroup(Base):
    __tablename__ = "organization_groups"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="groups")
    role_assignments: Mapped[list["ScopedRoleAssignment"]] = relationship(
        back_populates="group"
    )


class ScopedRoleAssignment(Base):
    __tablename__ = "scoped_role_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String, index=True)
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    group_id: Mapped[str | None] = mapped_column(
        ForeignKey("organization_groups.id"), nullable=True, index=True
    )

    organization: Mapped["Organization | None"] = relationship(
        back_populates="role_assignments"
    )
    group: Mapped["OrganizationGroup | None"] = relationship(
        back_populates="role_assignments"
    )


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "organization_id",
            "message_id",
            name="uq_emails_owner_message_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    message_id: Mapped[str] = mapped_column(String, index=True)
    thread_id: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )  # O3: email threading support
    fingerprint: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )
    sender: Mapped[str] = mapped_column(String)
    reply_to: Mapped[str | None] = mapped_column(String, nullable=True)
    recipients: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    in_reply_to: Mapped[str | None] = mapped_column(String, nullable=True)
    references: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="email", cascade="all, delete-orphan"
    )
    ticket_tasks: Mapped[list["TicketTask"]] = relationship(
        back_populates="related_email", cascade="all, delete-orphan"
    )


class TicketTask(Base):
    __tablename__ = "ticket_tasks"

    id: Mapped[int] = mapped_column("task_id", primary_key=True)
    task_uid: Mapped[str] = mapped_column(
        String(32), default=lambda: uuid.uuid4().hex, unique=True, index=True
    )
    user_id: Mapped[str] = mapped_column(String, index=True)
    organization_id: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )
    title: Mapped[str] = mapped_column("task_title", String)
    status: Mapped[str] = mapped_column(
        "status_code", String, default="open", index=True
    )
    priority: Mapped[str] = mapped_column(
        "priority_code", String, default="normal", index=True
    )
    source_type: Mapped[str] = mapped_column(String, default="email", index=True)
    related_email_id: Mapped[int | None] = mapped_column(
        "email_id", ForeignKey("emails.id"), nullable=True, index=True
    )
    related_thread_id: Mapped[str | None] = mapped_column(
        "thread_id", String, nullable=True, index=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    related_email: Mapped["Email | None"] = relationship(back_populates="ticket_tasks")


Index(
    "uq_ticket_tasks_reply_sla_email",
    TicketTask.user_id,
    func.coalesce(TicketTask.organization_id, ""),
    TicketTask.source_type,
    TicketTask.related_email_id,
    unique=True,
    postgresql_where=(
        (TicketTask.source_type == "reply_sla")
        & (TicketTask.related_email_id.is_not(None))
    ),
)


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"))
    filename: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))

    email: Mapped["Email"] = relationship(back_populates="attachments")


class TenantConfig(Base):
    __tablename__ = "tenant_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    organization_id: Mapped[str | None] = mapped_column(
        String,
        index=True,
        nullable=True,
    )

    # Email settings
    smtp_server: Mapped[str | None] = mapped_column(String, nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(nullable=True)
    smtp_username: Mapped[str | None] = mapped_column(String, nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    imap_server: Mapped[str | None] = mapped_column(String, nullable=True)
    imap_port: Mapped[int | None] = mapped_column(nullable=True)
    imap_username: Mapped[str | None] = mapped_column(String, nullable=True)
    imap_password: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    pop3_server: Mapped[str | None] = mapped_column(String, nullable=True)
    pop3_port: Mapped[int | None] = mapped_column(nullable=True)
    pop3_username: Mapped[str | None] = mapped_column(String, nullable=True)
    pop3_password: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)

    # OAuth and Third Party Settings
    oauth_client_id: Mapped[str | None] = mapped_column(String, nullable=True)
    oauth_client_secret: Mapped[str | None] = mapped_column(
        EncryptedString, nullable=True
    )
    oauth_redirect_uri: Mapped[str | None] = mapped_column(String, nullable=True)

    openai_api_key: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    google_client_id: Mapped[str | None] = mapped_column(String, nullable=True)
    google_client_secret: Mapped[str | None] = mapped_column(
        EncryptedString, nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<TenantConfig(id={self.id}, user_id='{self.user_id}', "
            f"organization_id='{self.organization_id}', "
            f"smtp_server='{self.smtp_server}', imap_server='{self.imap_server}', "
            f"has_smtp_password={self.smtp_password is not None}, "
            f"has_imap_password={self.imap_password is not None}, "
            f"has_pop3_password={self.pop3_password is not None}, "
            f"has_oauth_secret={self.oauth_client_secret is not None}, "
            f"has_openai_key={self.openai_api_key is not None}, "
            f"has_google_secret={self.google_client_secret is not None})>"
        )


Index(
    "uq_tenant_configs_owner_scope",
    TenantConfig.user_id,
    func.coalesce(TenantConfig.organization_id, ""),
    unique=True,
)


class SenderRelationship(Base):
    __tablename__ = "sender_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(
        String,
        index=True,
        nullable=True,
    )
    sender_email: Mapped[str] = mapped_column(String, index=True, nullable=False)
    parent_sender_email: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    source_message_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    source_thread_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    relationship_type: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float] = mapped_column(default=1.0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    __table_args__ = (
        Index(
            "uq_sender_relationships_scope_source",
            "user_id",
            func.coalesce(organization_id, ""),
            "sender_email",
            func.coalesce(source_message_id, ""),
            func.coalesce(source_thread_id, ""),
            unique=True,
        ),
    )


class CaldavAccount(Base):
    __tablename__ = "caldav_accounts"

    id: Mapped[int] = mapped_column("account_id", primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    server_url: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    credentials_encrypted: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class CalendarWritebackSource(Base):
    __tablename__ = "calendar_writeback_sources"

    source_uid: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    account_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_name: Mapped[str] = mapped_column(String, nullable=False)
    source_protocol: Mapped[str] = mapped_column(String, nullable=False)
    source_host: Mapped[str] = mapped_column(String, nullable=False)
    writeback_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    etag_value: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    __table_args__ = (
        Index(
            "ix_calendar_writeback_sources_scope",
            "user_id",
            "organization_id",
            "source_protocol",
        ),
    )


class ReplyTracker(Base):
    __tablename__ = "reply_trackers"

    id: Mapped[int] = mapped_column("tracker_id", primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    message_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status_code: Mapped[str] = mapped_column(String, default="waiting", index=True)
    follow_up_date: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class WebdavAccount(Base):
    __tablename__ = "webdav_accounts"

    id: Mapped[int] = mapped_column("account_id", primary_key=True)
    source_uid: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        default=lambda: f"webdav_src_{uuid.uuid4().hex}",
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    workspace_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    server_url: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    credentials_encrypted: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    writeback_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    etag_value: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class ProjectFolder(Base):
    __tablename__ = "project_folders"

    id: Mapped[int] = mapped_column("folder_id", primary_key=True)
    folder_uid: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        default=lambda: f"webdav_folder_{uuid.uuid4().hex}",
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    organization_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    project_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    webdav_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
