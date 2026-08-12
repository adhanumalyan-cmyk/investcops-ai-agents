"""
app/models/case.py

SQLAlchemy model for the structured PostgreSQL store (concept layer).
Optional at runtime: tables are only created when DATABASE_URL is configured.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Case(Base):
    """A single investigation case (mirrors the dashboard case list)."""

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    risk = Column(String, nullable=True)
    risk_score = Column(Integer, default=0)
    status = Column(String, default="Active Analysis")
    location = Column(String, nullable=True)
    assigned_officer = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    primary_vector = Column(String, nullable=True)
    evidence_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
