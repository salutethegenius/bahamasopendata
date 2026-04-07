"""SQLAlchemy database models for Bahamas Open Data."""
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text, 
    ForeignKey, Boolean, JSON, Index, Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class DocumentType(enum.Enum):
    """Types of source documents."""
    BUDGET_BOOK = "budget_book"
    MID_YEAR_STATEMENT = "mid_year_statement"
    DEBT_REPORT = "debt_report"
    REVENUE_REPORT = "revenue_report"
    AUDITOR_GENERAL = "auditor_general"
    HEALTH_STRATEGY = "health_strategy"
    OTHER = "other"


class Document(Base):
    """Source documents (PDFs) with provenance tracking."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_url = Column(Text)
    document_type = Column(String(50))
    fiscal_year = Column(String(10))  # e.g., "2024/25"
    downloaded_at = Column(DateTime, default=func.now())
    file_hash = Column(String(64))  # SHA-256 for integrity
    file_path = Column(Text)  # Path to stored file
    page_count = Column(Integer)
    is_ocr = Column(Boolean, default=False)
    extraction_status = Column(String(20), default="pending")
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document")
    budget_items = relationship("BudgetItem", back_populates="source_document")
    
    __table_args__ = (
        Index("idx_documents_fiscal_year", "fiscal_year"),
    )


class DocumentChunk(Base):
    """Document chunks for RAG embedding."""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    page_number = Column(Integer)
    content = Column(Text, nullable=False)
    chunk_type = Column(String(50))  # "text", "table", "header"
    embedding_id = Column(String(100))  # Pinecone vector ID
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
    )


class Ministry(Base):
    """Government ministries and departments."""
    __tablename__ = "ministries"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)  # e.g., "MOE"
    name = Column(String(255), nullable=False)
    sector = Column(String(100))  # "Education", "Health", etc.
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    budget_items = relationship("BudgetItem", back_populates="ministry")
    allocations = relationship("MinistryAllocation", back_populates="ministry")


class MinistryAllocation(Base):
    """Annual ministry budget allocations."""
    __tablename__ = "ministry_allocations"
    
    id = Column(Integer, primary_key=True)
    ministry_id = Column(Integer, ForeignKey("ministries.id"))
    fiscal_year = Column(String(10), nullable=False)
    total_allocation = Column(Float, nullable=False)
    recurrent_expenditure = Column(Float)
    capital_expenditure = Column(Float)
    salaries = Column(Float)
    programs = Column(Float)
    grants = Column(Float)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ministry = relationship("Ministry", back_populates="allocations")
    
    __table_args__ = (
        Index("idx_allocations_year", "fiscal_year"),
        Index("idx_allocations_ministry", "ministry_id"),
    )


class BudgetItem(Base):
    """Individual budget line items."""
    __tablename__ = "budget_items"
    
    id = Column(Integer, primary_key=True)
    ministry_id = Column(Integer, ForeignKey("ministries.id"))
    fiscal_year = Column(String(10), nullable=False)
    item_code = Column(String(50))
    item_name = Column(String(500), nullable=False)
    category = Column(String(100))  # "Salaries", "Supplies", "Capital", etc.
    amount = Column(Float, nullable=False)
    previous_year_amount = Column(Float)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ministry = relationship("Ministry", back_populates="budget_items")
    source_document = relationship("Document", back_populates="budget_items")
    
    __table_args__ = (
        Index("idx_items_fiscal_year", "fiscal_year"),
        Index("idx_items_ministry", "ministry_id"),
    )


class Revenue(Base):
    """Revenue collection data."""
    __tablename__ = "revenue"
    
    id = Column(Integer, primary_key=True)
    fiscal_year = Column(String(10), nullable=False)
    period = Column(String(20))  # "annual", "Q1", "Jul", etc.
    source_name = Column(String(255), nullable=False)  # "VAT", "Customs", etc.
    source_category = Column(String(100))  # "Tax", "Non-Tax", etc.
    amount = Column(Float, nullable=False)
    budget_estimate = Column(Float)  # What was budgeted
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index("idx_revenue_year", "fiscal_year"),
        Index("idx_revenue_source", "source_name"),
    )


class Debt(Base):
    """National debt records."""
    __tablename__ = "debt"
    
    id = Column(Integer, primary_key=True)
    fiscal_year = Column(String(10), nullable=False)
    as_of_date = Column(Date)
    total_debt = Column(Float, nullable=False)
    domestic_debt = Column(Float)
    external_debt = Column(Float)
    gdp = Column(Float)
    debt_to_gdp_ratio = Column(Float)
    annual_interest = Column(Float)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index("idx_debt_year", "fiscal_year"),
    )


class Creditor(Base):
    """Debt creditors."""
    __tablename__ = "creditors"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50))  # "domestic", "bilateral", "multilateral", "commercial"
    fiscal_year = Column(String(10), nullable=False)
    amount_owed = Column(Float, nullable=False)
    interest_rate = Column(Float)
    maturity_date = Column(Date)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime, default=func.now())


class NewsItem(Base):
    """Official news and announcements."""
    __tablename__ = "news_items"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    source = Column(String(255))  # "Ministry of Finance", "Auditor General", etc.
    url = Column(Text)
    published_date = Column(Date)
    summary = Column(Text)
    category = Column(String(100))  # "Budget", "Revenue", "Debt", etc.
    created_at = Column(DateTime, default=func.now())


class PublishedNewsItem(Base):
    """News items created from the document upload/publish workflow."""
    __tablename__ = "published_news_items"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    source = Column(String(255))
    url = Column(Text)
    published_date = Column(Date)
    summary = Column(Text)
    category = Column(String(100))
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_published_news_created", "created_at"),
        Index("idx_published_news_category", "category"),
    )


class EconomicIndicator(Base):
    """Economic indicators including income and cost of living data."""
    __tablename__ = "economic_indicators"
    
    id = Column(Integer, primary_key=True)
    indicator_type = Column(String(50), nullable=False)  # "middle_class", "working_class"
    island = Column(String(50), nullable=False)  # "new_providence", "grand_bahama"
    year = Column(Integer, nullable=False)
    month_amount = Column(Float, nullable=False)  # Monthly cost in USD
    annual_amount = Column(Float, nullable=False)  # Annual cost in USD
    breakdown = Column(JSON)  # JSON with categories: food, housing_utilities, nfnh, savings
    source_document = Column(String(500))
    source_url = Column(Text)
    author = Column(String(255))
    published_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index("idx_economic_indicator_type", "indicator_type"),
        Index("idx_economic_island", "island"),
        Index("idx_economic_year", "year"),
        Index("idx_economic_type_island_year", "indicator_type", "island", "year"),
    )


class PublishedEconomicIndicator(Base):
    """Economic indicators published from uploaded documents or structured data."""
    __tablename__ = "published_economic_indicators"

    id = Column(Integer, primary_key=True)
    indicator_type = Column(String(50), nullable=False)
    island = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    month_amount = Column(Float, nullable=False)
    annual_amount = Column(Float, nullable=False)
    breakdown = Column(JSON)
    source_document = Column(String(500))
    source_url = Column(Text)
    author = Column(String(255))
    published_date = Column(Date)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_published_economic_type", "indicator_type"),
        Index("idx_published_economic_island", "island"),
        Index("idx_published_economic_year", "year"),
        Index("idx_published_economic_type_island_year", "indicator_type", "island", "year"),
    )


class IslandAllocation(Base):
    """Published island-level allocations and profile data."""
    __tablename__ = "island_allocations"

    id = Column(Integer, primary_key=True)
    island_id = Column(String(80), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    capital = Column(String(255))
    population = Column(Integer)
    total_allocation = Column(Float, nullable=False, default=0.0)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    created_at = Column(DateTime, default=func.now())

    projects = relationship("IslandProject", back_populates="island", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_island_allocations_name", "name"),
    )


class IslandProject(Base):
    """Published capital/service projects associated with an island."""
    __tablename__ = "island_projects"

    id = Column(Integer, primary_key=True)
    island_id = Column(Integer, ForeignKey("island_allocations.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(500), nullable=False)
    category = Column(String(100))
    amount = Column(Float, nullable=False, default=0.0)
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    island = relationship("IslandAllocation", back_populates="projects")

    __table_args__ = (
        Index("idx_island_projects_island", "island_id"),
        Index("idx_island_projects_category", "category"),
    )
    

class Poll(Base):
    """Polling questions for public data collection."""
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True)
    question = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")  # "draft", "active", "closed"
    domain = Column(String(50))  # "budget", "health", "income", etc.
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")


class PollOption(Base):
    """Options for a poll."""
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    poll = relationship("Poll", back_populates="options")
    votes = relationship("PollVote", back_populates="option", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_poll_options_poll_id", "poll_id"),
    )


class PollVote(Base):
    """Individual poll votes."""
    __tablename__ = "poll_votes"

    id = Column(Integer, primary_key=True)
    poll_id = Column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    option_id = Column(Integer, ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False)
    fingerprint = Column(String(255))  # hashed identifier or client token
    created_at = Column(DateTime, default=func.now())

    poll = relationship("Poll", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")

    __table_args__ = (
        Index("idx_poll_votes_poll_id", "poll_id"),
        Index("idx_poll_votes_option_id", "option_id"),
        Index(
            "uq_poll_vote_fingerprint",
            "poll_id",
            "fingerprint",
            unique=True,
        ),
    )


class AdminUser(Base):
    """Admin users who can manage data via the admin panel."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), nullable=False)  # "superuser" or "admin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_keys = relationship("IngestionApiKey", back_populates="created_by_user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """JWT refresh tokens for session management."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)  # SHA-256 of raw token
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    revoked_at = Column(DateTime)
    ip_address = Column(String(45))  # IPv6-safe length

    user = relationship("AdminUser", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_hash", "token_hash"),
    )


class IngestionApiKey(Base):
    """Long-lived API keys for ingestion clients, agents, and scripts."""
    __tablename__ = "ingestion_api_keys"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    key_prefix = Column(String(32), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime)
    revoked_at = Column(DateTime)

    created_by_user = relationship("AdminUser", back_populates="api_keys")


class AuditLog(Base):
    """Audit trail for all admin actions."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"))
    action = Column(String(50), nullable=False)  # create, update, delete, login, upload
    resource_type = Column(String(50), nullable=False)  # e.g. "budget_items", "user", "poll"
    resource_id = Column(String(50))
    details = Column(JSON)  # diff or payload summary
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=func.now())

    user = relationship("AdminUser", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_user_created", "user_id", "created_at"),
        Index("idx_audit_resource_created", "resource_type", "created_at"),
    )
