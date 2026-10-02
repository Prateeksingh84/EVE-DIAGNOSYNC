from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & BI"])


@router.get(
    "/overview",
    summary="Admin Business Intelligence & KPIs",
    description="Retrieve executive KPIs, conversion rates, diagnostic centre volume, test popularity, and revenue aggregates. (Admin only)",
)
async def get_analytics_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    data = await analytics_service.get_overview_analytics(db)
    return data


@router.get(
    "/export",
    summary="Export Bookings Audit Report (CSV)",
    description="Stream an executive CSV report containing complete booking histories, transaction IDs, and patient records. (Admin only)",
)
async def export_bookings_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    csv_data = await analytics_service.export_bookings_csv(db)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"eve_bookings_report_{timestamp}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
