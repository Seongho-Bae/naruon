from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, ForeignKey
from pgvector.sqlalchemy import Vector
import datetime

Base = declarative_base()


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    sender: Mapped[str] = mapped_column(String)
    recipients: Mapped[str | None] = mapped_column(String, nullable=True)
    subject: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text)
    thread_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
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
    imap_server: Mapped[str | None] = mapped_column(String, nullable=True)
    imap_port: Mapped[int | None] = mapped_column(nullable=True)
    pop3_server: Mapped[str | None] = mapped_column(String, nullable=True)
    pop3_port: Mapped[int | None] = mapped_column(nullable=True)
    
    # OAuth and Third Party Settings
    oauth_client_id: Mapped[str | None] = mapped_column(String, nullable=True)
    oauth_client_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    oauth_redirect_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    
    openai_api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    google_client_id: Mapped[str | None] = mapped_column(String, nullable=True)
    google_client_secret: Mapped[str | None] = mapped_column(String, nullable=True)
