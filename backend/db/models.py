from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.types import TypeDecorator
from cryptography.fernet import Fernet
from core.config import settings
from pgvector.sqlalchemy import Vector
import datetime
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_fernet() -> Fernet:
    if settings.ENCRYPTION_KEY:
        key = settings.ENCRYPTION_KEY.get_secret_value().encode()
        try:
            return Fernet(key)
        except ValueError:
            key_b64 = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
            return Fernet(key_b64)
    raise RuntimeError("ENCRYPTION_KEY is required to encrypt secrets")


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
            f = get_fernet()
            return f.encrypt(value.encode("utf-8")).decode("utf-8")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            f = get_fernet()
            try:
                return f.decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:
                logger.warning("Failed to decrypt field in EncryptedString")
                return value
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


class LLMProvider(Base):
    __tablename__ = "llm_providers"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name", name="uq_llm_providers_organization_name"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
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
    organization_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
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


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "mailbox_account_id",
            "message_id",
            name="uq_emails_owner_mailbox_message",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    mailbox_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("mailbox_accounts.id"), index=True, nullable=True
    )
    message_id: Mapped[str] = mapped_column(String, index=True)
    thread_id: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )  # O3: email threading support
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
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True)

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
            f"smtp_server='{self.smtp_server}', imap_server='{self.imap_server}', "
            f"has_smtp_password={self.smtp_password is not None}, "
            f"has_imap_password={self.imap_password is not None}, "
            f"has_oauth_secret={self.oauth_client_secret is not None}, "
            f"has_openai_key={self.openai_api_key is not None}, "
            f"has_google_secret={self.google_client_secret is not None})>"
        )


class MailboxAccount(Base):
    __tablename__ = "mailbox_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "email_address", name="uq_mailbox_accounts_user_email"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    email_address: Mapped[str] = mapped_column(String, index=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    provider: Mapped[str] = mapped_column(String, default="custom")
    is_default_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    def __repr__(self) -> str:
        password_flags = (
            f"has_smtp_password={self.smtp_password is not None}, "
            f"has_imap_password={self.imap_password is not None}, "
            f"has_pop3_password={self.pop3_password is not None}"
        )
        return (
            f"<MailboxAccount(id={self.id}, user_id='{self.user_id}', "
            f"email_address='{self.email_address}', provider='{self.provider}', "
            f"is_default_reply={self.is_default_reply}, "
            f"is_active={self.is_active}, {password_flags})>"
        )


class ExecutionItem(Base):
    __tablename__ = "execution_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "workspace_id",
            "source_email_id",
            name="uq_execution_items_user_workspace_email",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    organization_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    workspace_id: Mapped[str] = mapped_column(String, index=True)
    source_mailbox_account_id: Mapped[int | None] = mapped_column(
        nullable=True, index=True
    )
    source_email_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    source_thread_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    source_message_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    source_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String)
    sender: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="queued", index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
