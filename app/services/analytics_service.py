import csv
import io
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.diagnostic import DiagnosticCentre, DiagnosticTest, CentreTest
from app.models.user import User


async def get_overview_analytics(db: AsyncSession) -> Dict[str, Any]:
    """Calculate business analytics, KPIs, and revenue metrics."""
    # 1. Total Users
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0

    # 2. Total Centres & Tests
    centres_count = (await db.execute(select(func.count(DiagnosticCentre.id)))).scalar() or 0
    tests_count = (await db.execute(select(func.count(DiagnosticTest.id)))).scalar() or 0

    # 3. Total Bookings & Status Breakdown
    bookings_count = (await db.execute(select(func.count(Booking.id)))).scalar() or 0

    status_counts_raw = (
        await db.execute(
            select(Booking.status, func.count(Booking.id))
            .group_by(Booking.status)
        )
    ).all()
    status_counts = {str(row[0].value if hasattr(row[0], "value") else row[0]): row[1] for row in status_counts_raw}

    confirmed_count = status_counts.get("CONFIRMED", 0)
    pending_count = status_counts.get("PENDING", 0)
    failed_count = status_counts.get("FAILED", 0)
    cancelled_count = status_counts.get("CANCELLED", 0)

    # 4. Total Revenue (sum of successful payments)
    rev_result = (
        await db.execute(
            select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.SUCCESS)
        )
    ).scalar()
    total_revenue = float(rev_result or Decimal("0.00"))

    # Conversion Rate
    conversion_rate = (confirmed_count / bookings_count * 100) if bookings_count > 0 else 0.0

    # 5. Top Diagnostic Centres by Booking Volume
    top_centres_query = (
        select(
            DiagnosticCentre.name,
            DiagnosticCentre.city,
            func.count(Booking.id).label("booking_count"),
            func.sum(Booking.amount).label("total_sales"),
        )
        .join(CentreTest, DiagnosticCentre.id == CentreTest.centre_id)
        .join(Booking, CentreTest.id == Booking.centre_test_id)
        .group_by(DiagnosticCentre.id, DiagnosticCentre.name, DiagnosticCentre.city)
        .order_by(desc("booking_count"))
        .limit(5)
    )
    top_centres_raw = (await db.execute(top_centres_query)).all()
    top_centres = [
        {
            "centre_name": r[0],
            "city": r[1],
            "bookings": r[2],
            "revenue": float(r[3] or 0),
        }
        for r in top_centres_raw
    ]

    # 6. Top Tests by Popularity
    top_tests_query = (
        select(
            DiagnosticTest.name,
            DiagnosticTest.category,
            func.count(Booking.id).label("booking_count"),
        )
        .join(CentreTest, DiagnosticTest.id == CentreTest.test_id)
        .join(Booking, CentreTest.id == Booking.centre_test_id)
        .group_by(DiagnosticTest.id, DiagnosticTest.name, DiagnosticTest.category)
        .order_by(desc("booking_count"))
        .limit(5)
    )
    top_tests_raw = (await db.execute(top_tests_query)).all()
    top_tests = [
        {"test_name": r[0], "category": r[1] or "General", "bookings": r[2]}
        for r in top_tests_raw
    ]

    # 7. Recent Transactions / Bookings
    recent_bookings_query = (
        select(Booking)
        .options(
            selectinload(Booking.user),
            selectinload(Booking.centre_test).selectinload(CentreTest.centre),
            selectinload(Booking.centre_test).selectinload(CentreTest.test),
        )
        .order_by(Booking.created_at.desc())
        .limit(10)
    )
    recent_bookings = (await db.execute(recent_bookings_query)).scalars().all()

    recent_items = []
    for b in recent_bookings:
        recent_items.append({
            "booking_id": str(b.id),
            "reference": b.booking_reference,
            "patient_name": b.user.full_name if b.user else "Unknown",
            "patient_email": b.user.email if b.user else "Unknown",
            "centre": b.centre_test.centre.name if b.centre_test and b.centre_test.centre else "N/A",
            "test": b.centre_test.test.name if b.centre_test and b.centre_test.test else "N/A",
            "amount": float(b.amount),
            "status": b.status.value,
            "appointment": b.appointment_datetime.isoformat(),
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })

    return {
        "kpis": {
            "total_revenue": total_revenue,
            "total_bookings": bookings_count,
            "confirmed_bookings": confirmed_count,
            "pending_bookings": pending_count,
            "failed_bookings": failed_count,
            "cancelled_bookings": cancelled_count,
            "conversion_rate_percent": round(conversion_rate, 1),
            "total_users": users_count,
            "total_centres": centres_count,
            "total_tests": tests_count,
        },
        "top_centres": top_centres,
        "top_tests": top_tests,
        "recent_bookings": recent_items,
    }


async def export_bookings_csv(db: AsyncSession) -> str:
    """Generate a CSV string of all bookings with full audit information."""
    query = (
        select(Booking)
        .options(
            selectinload(Booking.user),
            selectinload(Booking.centre_test).selectinload(CentreTest.centre),
            selectinload(Booking.centre_test).selectinload(CentreTest.test),
            selectinload(Booking.payments),
        )
        .order_by(Booking.created_at.desc())
    )
    result = await db.execute(query)
    bookings = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "Booking Reference",
        "Booking Date (UTC)",
        "Appointment Datetime",
        "Patient Name",
        "Patient Email",
        "Diagnostic Centre",
        "City",
        "Diagnostic Test",
        "Amount (INR)",
        "Booking Status",
        "Transaction ID",
        "Payment Status",
        "Payment Method",
    ])

    for b in bookings:
        patient_name = b.user.full_name if b.user else "N/A"
        patient_email = b.user.email if b.user else "N/A"
        centre_name = b.centre_test.centre.name if b.centre_test and b.centre_test.centre else "N/A"
        city = b.centre_test.centre.city if b.centre_test and b.centre_test.centre else "N/A"
        test_name = b.centre_test.test.name if b.centre_test and b.centre_test.test else "N/A"

        txn_id = "N/A"
        pay_status = "N/A"
        pay_method = "N/A"
        if b.payments:
            p = b.payments[-1]
            txn_id = p.transaction_id
            pay_status = p.status.value
            pay_method = p.payment_method

        writer.writerow([
            b.booking_reference,
            b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else "",
            b.appointment_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            patient_name,
            patient_email,
            centre_name,
            city,
            test_name,
            str(b.amount),
            b.status.value,
            txn_id,
            pay_status,
            pay_method,
        ])

    return output.getvalue()
