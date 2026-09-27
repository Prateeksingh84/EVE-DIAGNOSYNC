import math
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.diagnostic import (
    DiagnosticCentre,
    DiagnosticTest,
    CentreTest,
)
from app.schemas.diagnostic import (
    DiagnosticCentreCreate,
    DiagnosticCentreUpdate,
    DiagnosticCentreResponse,
    DiagnosticTestCreate,
    DiagnosticTestResponse,
    CentreTestCreate,
    CentreTestResponse,
)
from app.utils.exceptions import NotFoundException, ConflictException
from app.utils.pagination import PaginatedResponse
from app.services.cache_service import cache_get, cache_set, cache_delete_pattern

router = APIRouter(prefix="/diagnostics", tags=["Diagnostic Centres & Tests"])


# ─── Diagnostic Centres ───────────────────────────────────────────────

@router.post(
    "/centres",
    response_model=DiagnosticCentreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic centre (Admin)",
)
async def create_centre(
    centre_data: DiagnosticCentreCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin_user)],
):
    centre = DiagnosticCentre(**centre_data.model_dump())
    db.add(centre)
    await db.flush()
    await db.refresh(centre)
    await cache_delete_pattern("centres:*")
    return centre


@router.get(
    "/centres",
    response_model=PaginatedResponse[DiagnosticCentreResponse],
    summary="List all diagnostic centres",
)
async def list_centres(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city: Optional[str] = Query(default=None, description="Filter by city"),
    search: Optional[str] = Query(default=None, description="Search by name"),
):
    cache_key = f"centres:list:{page}:{page_size}:{city}:{search}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    query = select(DiagnosticCentre).options(
        selectinload(DiagnosticCentre.centre_tests).selectinload(
            CentreTest.test
        )
    ).where(DiagnosticCentre.is_active == True)

    count_query = select(func.count()).select_from(DiagnosticCentre).where(
        DiagnosticCentre.is_active == True
    )

    if city:
        query = query.where(
            DiagnosticCentre.city.ilike(f"%{city}%")
        )
        count_query = count_query.where(
            DiagnosticCentre.city.ilike(f"%{city}%")
        )

    if search:
        query = query.where(
            DiagnosticCentre.name.ilike(f"%{search}%")
        )
        count_query = count_query.where(
            DiagnosticCentre.name.ilike(f"%{search}%")
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    offset = (page - 1) * page_size
    query = query.order_by(DiagnosticCentre.name).offset(offset).limit(
        page_size
    )
    result = await db.execute(query)
    centres = list(result.scalars().all())

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    response_data = {
        "items": [DiagnosticCentreResponse.model_validate(c).model_dump(mode="json") for c in centres],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }

    await cache_set(cache_key, response_data, ttl=120)
    return response_data


@router.get(
    "/centres/{centre_id}",
    response_model=DiagnosticCentreResponse,
    summary="Get a diagnostic centre by ID",
)
async def get_centre(
    centre_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    cache_key = f"centres:detail:{centre_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(
        select(DiagnosticCentre)
        .options(
            selectinload(DiagnosticCentre.centre_tests).selectinload(
                CentreTest.test
            )
        )
        .where(DiagnosticCentre.id == centre_id)
    )
    centre = result.scalar_one_or_none()

    if not centre:
        raise NotFoundException(
            resource="Diagnostic Centre", resource_id=str(centre_id)
        )

    response_data = DiagnosticCentreResponse.model_validate(centre).model_dump(mode="json")
    await cache_set(cache_key, response_data, ttl=300)
    return response_data


@router.put(
    "/centres/{centre_id}",
    response_model=DiagnosticCentreResponse,
    summary="Update a diagnostic centre (Admin)",
)
async def update_centre(
    centre_id: UUID,
    update_data: DiagnosticCentreUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin_user)],
):
    result = await db.execute(
        select(DiagnosticCentre).where(
            DiagnosticCentre.id == centre_id
        )
    )
    centre = result.scalar_one_or_none()

    if not centre:
        raise NotFoundException(
            resource="Diagnostic Centre", resource_id=str(centre_id)
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(centre, key, value)

    await db.flush()
    await db.refresh(centre)
    await cache_delete_pattern("centres:*")
    return centre


# ─── Diagnostic Tests ─────────────────────────────────────────────────

@router.post(
    "/tests",
    response_model=DiagnosticTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a diagnostic test (Admin)",
)
async def create_test(
    test_data: DiagnosticTestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin_user)],
):
    test = DiagnosticTest(**test_data.model_dump())
    db.add(test)
    await db.flush()
    await db.refresh(test)
    return test


@router.get(
    "/tests",
    response_model=PaginatedResponse[DiagnosticTestResponse],
    summary="List all diagnostic tests",
)
async def list_tests(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(
        default=None, description="Filter by category"
    ),
    search: Optional[str] = Query(
        default=None, description="Search by name"
    ),
):
    query = select(DiagnosticTest)
    count_query = select(func.count()).select_from(DiagnosticTest)

    if category:
        query = query.where(
            DiagnosticTest.category.ilike(f"%{category}%")
        )
        count_query = count_query.where(
            DiagnosticTest.category.ilike(f"%{category}%")
        )

    if search:
        query = query.where(
            DiagnosticTest.name.ilike(f"%{search}%")
        )
        count_query = count_query.where(
            DiagnosticTest.name.ilike(f"%{search}%")
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    offset = (page - 1) * page_size
    query = query.order_by(DiagnosticTest.name).offset(offset).limit(
        page_size
    )
    result = await db.execute(query)
    tests = list(result.scalars().all())

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "items": tests,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


# ─── Centre-Test Association ──────────────────────────────────────────

@router.post(
    "/centres/{centre_id}/tests",
    response_model=CentreTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a test to a centre with pricing (Admin)",
)
async def add_test_to_centre(
    centre_id: UUID,
    data: CentreTestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(get_current_admin_user)],
):
    # Verify centre exists
    centre_result = await db.execute(
        select(DiagnosticCentre).where(
            DiagnosticCentre.id == centre_id
        )
    )
    if not centre_result.scalar_one_or_none():
        raise NotFoundException(
            resource="Diagnostic Centre", resource_id=str(centre_id)
        )

    # Verify test exists
    test_result = await db.execute(
        select(DiagnosticTest).where(
            DiagnosticTest.id == data.test_id
        )
    )
    if not test_result.scalar_one_or_none():
        raise NotFoundException(
            resource="Diagnostic Test", resource_id=str(data.test_id)
        )

    # Check for duplicate
    existing = await db.execute(
        select(CentreTest).where(
            CentreTest.centre_id == centre_id,
            CentreTest.test_id == data.test_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(
            detail="This test is already associated with this centre"
        )

    centre_test = CentreTest(
        centre_id=centre_id,
        test_id=data.test_id,
        price=data.price,
    )
    db.add(centre_test)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(CentreTest)
        .options(selectinload(CentreTest.test))
        .where(CentreTest.id == centre_test.id)
    )
    centre_test = result.scalar_one()

    await cache_delete_pattern("centres:*")
    return centre_test


@router.get(
    "/centres/{centre_id}/tests",
    response_model=list[CentreTestResponse],
    summary="List tests available at a centre",
)
async def list_centre_tests(
    centre_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Verify centre exists
    centre_result = await db.execute(
        select(DiagnosticCentre).where(
            DiagnosticCentre.id == centre_id
        )
    )
    if not centre_result.scalar_one_or_none():
        raise NotFoundException(
            resource="Diagnostic Centre", resource_id=str(centre_id)
        )

    result = await db.execute(
        select(CentreTest)
        .options(selectinload(CentreTest.test))
        .where(
            CentreTest.centre_id == centre_id,
            CentreTest.is_available == True,
        )
    )
    return list(result.scalars().all())
