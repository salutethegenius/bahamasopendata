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


class UserFeedback(Base):
    """User-submitted data corrections and feedback."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True)
    feedback_type = Column(String(50))  # "correction", "question", "suggestion"
    related_table = Column(String(100))
    related_id = Column(Integer)
    description = Column(Text, nullable=False)
    submitted_by = Column(String(255))
    email = Column(String(255))
    status = Column(String(20), default="pending")  # "pending", "reviewed", "resolved"
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)


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

