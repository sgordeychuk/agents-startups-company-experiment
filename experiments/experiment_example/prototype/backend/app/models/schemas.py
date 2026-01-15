from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration for RBAC."""

    FISHER = "fisher"
    BUYER_ADMIN = "buyer_admin"
    BUYER_VIEWER = "buyer_viewer"
    SYSTEM_ADMIN = "system_admin"


class CatchMethod(str, Enum):
    """Catch method enumeration."""

    TRAWL = "trawl"
    LONGLINE = "longline"
    GILLNET = "gillnet"
    PURSE_SEINE = "purse_seine"
    TRAP = "trap"
    HANDLINE = "handline"


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
    """Login response schema with JWT token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    email: str = Field(..., description="User email")


class GPSLocation(BaseModel):
    """GPS location schema."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    accuracy: float | None = Field(None, description="GPS accuracy in meters")


class CatchCreate(BaseModel):
    """Schema for creating a new catch record."""

    vessel_id: str = Field(..., min_length=3, description="Vessel identification number")
    species: str = Field(..., min_length=2, description="Species name or code")
    quantity: float = Field(..., gt=0, description="Catch quantity in kg")
    catch_method: CatchMethod = Field(..., description="Method used to catch")
    location: GPSLocation = Field(..., description="GPS location of catch")
    catch_timestamp: datetime = Field(..., description="Timestamp when catch was made")
    notes: str | None = Field(None, max_length=500, description="Additional notes")


class CatchResponse(BaseModel):
    """Schema for catch record response."""

    id: str = Field(..., description="Catch record ID")
    vessel_id: str = Field(..., description="Vessel identification number")
    species: str = Field(..., description="Species name")
    quantity: float = Field(..., description="Catch quantity in kg")
    catch_method: CatchMethod = Field(..., description="Method used to catch")
    location: GPSLocation = Field(..., description="GPS location of catch")
    catch_timestamp: datetime = Field(..., description="Timestamp of catch")
    created_at: datetime = Field(..., description="Record creation timestamp")
    fisher_id: str = Field(..., description="Fisher user ID")
    buyer_id: str | None = Field(None, description="Associated buyer ID")
    notes: str | None = Field(None, description="Additional notes")
    is_verified: bool = Field(default=False, description="GPS verification status")
    compliance_status: str = Field(..., description="SIMP compliance status")

    class Config:
        from_attributes = True


class CatchListResponse(BaseModel):
    """Schema for paginated catch list response."""

    total: int = Field(..., description="Total number of catches")
    catches: list[CatchResponse] = Field(..., description="List of catch records")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Items per page")


class SupplyChainMapPoint(BaseModel):
    """Schema for supply chain map visualization."""

    catch_id: str
    location: GPSLocation
    species: str
    quantity: float
    catch_timestamp: datetime
    vessel_id: str


class SupplyChainMapResponse(BaseModel):
    """Schema for supply chain map data."""

    points: list[SupplyChainMapPoint] = Field(..., description="Map points for visualization")
    total_quantity: float = Field(..., description="Total catch quantity in kg")
    species_count: int = Field(..., description="Number of unique species")
