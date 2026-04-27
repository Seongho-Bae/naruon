from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text
from pgvector.sqlalchemy import Vector
import datetime

Base = declarative_base()

class Email(Base):
    __tablename__ = "emails"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    sender: Mapped[str] = mapped_column(String)
    recipients: Mapped[str] = mapped_column(String, nullable=True)
    subject: Mapped[str] = mapped_column(String, nullable=True)
    date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    body: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(1536))
