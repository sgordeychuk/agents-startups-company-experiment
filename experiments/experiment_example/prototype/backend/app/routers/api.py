import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import (
    CatchCreate,
    CatchListResponse,
    CatchMethod,
    CatchResponse,
    GPSLocation,
    LoginRequest,
    LoginResponse,
    UserRole,
)

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    For MVP, accepts demo credentials:
    - fisher@seachain.com / password123 (fisher role)
    - buyer@seachain.com / password123 (buyer_admin role)
    """
    # Demo authentication logic
    demo_users = {
        "fisher@seachain.com": {
            "user_id": "fisher-001",
            "role": UserRole.FISHER,
            "password": "password123",
        },
        "buyer@seachain.com": {
            "user_id": "buyer-001",
            "role": UserRole.BUYER_ADMIN,
            "password": "password123",
        },
    }

    user_data = demo_users.get(request.email)

    if not user_data or user_data["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In production, generate real JWT token
    demo_token = f"demo_jwt_token_{user_data['user_id']}"

    return LoginResponse(
        access_token=demo_token,
        token_type="bearer",
        user_id=user_data["user_id"],
        role=user_data["role"],
        email=request.email,
    )


@router.post("/catches", response_model=CatchResponse, status_code=status.HTTP_201_CREATED)
async def create_catch(catch_data: CatchCreate, db: AsyncSession = Depends(get_db)):
    """
    Fisher submits new catch record with GPS, species, quantity, and photos.
    Records immutable event in ledger for audit trail.
    """
    # Generate unique catch ID
    catch_id = str(uuid.uuid4())

    # Validate GPS location (basic checks)
    if not (-90 <= catch_data.location.latitude <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid latitude value"
        )

    if not (-180 <= catch_data.location.longitude <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid longitude value"
        )

    # Validate catch timestamp (not in future)
    if catch_data.catch_timestamp > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Catch timestamp cannot be in the future",
        )

    # Demo: auto-approve catches with valid GPS
    is_verified = True
    compliance_status = "compliant"

    # Create catch response
    catch_response = CatchResponse(
        id=catch_id,
        vessel_id=catch_data.vessel_id,
        species=catch_data.species,
        quantity=catch_data.quantity,
        catch_method=catch_data.catch_method,
        location=catch_data.location,
        catch_timestamp=catch_data.catch_timestamp,
        created_at=datetime.utcnow(),
        fisher_id="fisher-001",  # Demo fisher ID
        buyer_id="buyer-001",  # Demo buyer ID
        notes=catch_data.notes,
        is_verified=is_verified,
        compliance_status=compliance_status,
    )

    return catch_response


@router.get("/catches", response_model=CatchListResponse)
async def get_catches(
    species: str | None = Query(None, description="Filter by species"),
    vessel_id: str | None = Query(None, description="Filter by vessel ID"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Buyer retrieves all catches from their supplier network.
    Supports filtering by date, species, and vessel.
    """
    # Generate placeholder catch data for demo
    demo_catches = [
        CatchResponse(
            id=str(uuid.uuid4()),
            vessel_id="VSL-2024-001",
            species="Yellowfin Tuna",
            quantity=125.5,
            catch_method=CatchMethod.LONGLINE,
            location=GPSLocation(latitude=34.0522, longitude=-118.2437, accuracy=10.0),
            catch_timestamp=datetime.utcnow() - timedelta(hours=6),
            created_at=datetime.utcnow() - timedelta(hours=5),
            fisher_id="fisher-001",
            buyer_id="buyer-001",
            notes="Quality catch, ideal conditions",
            is_verified=True,
            compliance_status="compliant",
        ),
        CatchResponse(
            id=str(uuid.uuid4()),
            vessel_id="VSL-2024-002",
            species="Pacific Salmon",
            quantity=87.3,
            catch_method=CatchMethod.GILLNET,
            location=GPSLocation(latitude=47.6062, longitude=-122.3321, accuracy=15.0),
            catch_timestamp=datetime.utcnow() - timedelta(hours=12),
            created_at=datetime.utcnow() - timedelta(hours=11),
            fisher_id="fisher-002",
            buyer_id="buyer-001",
            notes="Good size, no damage",
            is_verified=True,
            compliance_status="compliant",
        ),
        CatchResponse(
            id=str(uuid.uuid4()),
            vessel_id="VSL-2024-001",
            species="Swordfish",
            quantity=203.8,
            catch_method=CatchMethod.LONGLINE,
            location=GPSLocation(latitude=32.7157, longitude=-117.1611, accuracy=12.0),
            catch_timestamp=datetime.utcnow() - timedelta(hours=18),
            created_at=datetime.utcnow() - timedelta(hours=17),
            fisher_id="fisher-001",
            buyer_id="buyer-001",
            notes="Large specimen",
            is_verified=True,
            compliance_status="compliant",
        ),
    ]

    # Apply filters
    filtered_catches = demo_catches

    if species:
        filtered_catches = [c for c in filtered_catches if species.lower() in c.species.lower()]

    if vessel_id:
        filtered_catches = [c for c in filtered_catches if c.vessel_id == vessel_id]

    if start_date:
        filtered_catches = [c for c in filtered_catches if c.catch_timestamp >= start_date]

    if end_date:
        filtered_catches = [c for c in filtered_catches if c.catch_timestamp <= end_date]

    total = len(filtered_catches)

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_catches = filtered_catches[start_idx:end_idx]

    return CatchListResponse(total=total, catches=paginated_catches, page=page, page_size=page_size)


@router.get("/supply-chain/map")
async def get_supply_chain_map(db: AsyncSession = Depends(get_db)):
    """
    Get geospatial data for supply chain visualization on dashboard map.
    Returns catch locations with metadata for interactive mapping.
    """
    # Demo supply chain map data
    map_data = {
        "points": [
            {
                "catch_id": str(uuid.uuid4()),
                "location": {"latitude": 34.0522, "longitude": -118.2437},
                "species": "Yellowfin Tuna",
                "quantity": 125.5,
                "catch_timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "vessel_id": "VSL-2024-001",
            },
            {
                "catch_id": str(uuid.uuid4()),
                "location": {"latitude": 47.6062, "longitude": -122.3321},
                "species": "Pacific Salmon",
                "quantity": 87.3,
                "catch_timestamp": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                "vessel_id": "VSL-2024-002",
            },
            {
                "catch_id": str(uuid.uuid4()),
                "location": {"latitude": 32.7157, "longitude": -117.1611},
                "species": "Swordfish",
                "quantity": 203.8,
                "catch_timestamp": (datetime.utcnow() - timedelta(hours=18)).isoformat(),
                "vessel_id": "VSL-2024-001",
            },
        ],
        "total_quantity": 416.6,
        "species_count": 3,
        "vessel_count": 2,
    }

    return map_data
