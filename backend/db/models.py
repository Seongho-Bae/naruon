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
    in_reply_to: Mapped[str | None] = mapped_column(String, nullable=True)
    references: Mapped[str | None] = mapped_column(String, nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="email", cascade="all, delete-orphan")

class Attachment(Base):
    __tablename__ = "attachments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"))
    filename: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))
    
    email: Mapped["Email"] = relationship(back_populates="attachments")
