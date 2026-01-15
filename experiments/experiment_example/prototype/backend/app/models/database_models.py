import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    FISHER = "fisher"
    BUYER_ADMIN = "buyer_admin"
    BUYER_VIEWER = "buyer_viewer"
    SYSTEM_ADMIN = "system_admin"


class CatchMethod(str, enum.Enum):
    """Catch method enumeration."""

    TRAWL = "trawl"
    LONGLINE = "longline"
    GILLNET = "gillnet"
    PURSE_SEINE = "purse_seine"
    TRAP = "trap"
    HANDLINE = "handline"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    full_name = Column(String, nullable=True)
    buyer_id = Column(String, ForeignKey("users.id"), nullable=True)  # For fishers linked to buyers
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)


class Catch(Base):
    """Catch record model for storing harvest data."""

    __tablename__ = "catches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fisher_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    buyer_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    vessel_id = Column(String, nullable=False, index=True)
    species = Column(String, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    catch_method = Column(SQLEnum(CatchMethod), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    gps_accuracy = Column(Float, nullable=True)
    catch_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    compliance_status = Column(String, default="pending")


class LedgerEvent(Base):
    """Immutable ledger event model for audit trail."""

    __tablename__ = "ledger_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)  # catch_id, user_id, etc.
    entity_type = Column(String, nullable=False)
    event_data = Column(Text, nullable=False)  # JSON string
    previous_hash = Column(String, nullable=True)
    current_hash = Column(String, nullable=False, unique=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
