import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db, engine
from app.models.user import User
from app.models.diagnostic import DiagnosticCentre, DiagnosticTest, CentreTest
from app.security import hash_password
import structlog

logger = structlog.get_logger(__name__)


async def seed_data():
    """Seed sample data for demo and evaluation."""
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            logger.info("Database already seeded. Skipping.")
            return {"status": "already_seeded", "message": "Database already contains data."}

        logger.info("Seeding database with demo diagnostic centres, tests, and users...")

        # 1. Create Users
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@evehealthcare.com",
            full_name="Admin Director",
            phone="+919876543210",
            hashed_password=hash_password("AdminPass123!"),
            is_active=True,
            is_admin=True,
        )
        patient_user = User(
            id=uuid.uuid4(),
            email="patient@evehealthcare.com",
            full_name="John Doe (Patient)",
            phone="+919812345678",
            hashed_password=hash_password("PatientPass123!"),
            is_active=True,
            is_admin=False,
        )
        session.add_all([admin_user, patient_user])
        await session.flush()

        # 2. Create Diagnostic Centres
        centre1 = DiagnosticCentre(
            id=uuid.uuid4(),
            name="Apollo Diagnostics Centre",
            address="Plot 14, Bandra Kurla Complex",
            city="Mumbai",
            state="Maharashtra",
            pincode="400051",
            phone="+912261234567",
            email="bandra@apollodiagnostics.com",
            is_active=True,
        )
        centre2 = DiagnosticCentre(
            id=uuid.uuid4(),
            name="Metropolis Healthcare Lab",
            address="Sector 18, Connaught Place",
            city="New Delhi",
            state="Delhi",
            pincode="110001",
            phone="+911145678901",
            email="delhi@metropolis.com",
            is_active=True,
        )
        centre3 = DiagnosticCentre(
            id=uuid.uuid4(),
            name="Dr. Lal PathLabs",
            address="100 Feet Road, Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            phone="+918023456789",
            email="indiranagar@lalpathlabs.com",
            is_active=True,
        )
        session.add_all([centre1, centre2, centre3])
        await session.flush()

        # 3. Create Diagnostic Tests
        test_cbc = DiagnosticTest(
            id=uuid.uuid4(),
            name="Complete Blood Count (CBC)",
            description="Evaluates overall health and detects a wide range of disorders including anemia and infection.",
            category="Hematology",
        )
        test_lipid = DiagnosticTest(
            id=uuid.uuid4(),
            name="Lipid Profile (Cholesterol)",
            description="Measures total cholesterol, HDL, LDL, and triglycerides to assess cardiovascular risk.",
            category="Biochemistry",
        )
        test_thyroid = DiagnosticTest(
            id=uuid.uuid4(),
            name="Thyroid Profile (T3, T4, TSH)",
            description="Assesses thyroid gland function and metabolism rate.",
            category="Endocrinology",
        )
        test_hba1c = DiagnosticTest(
            id=uuid.uuid4(),
            name="HbA1c Glycated Hemoglobin",
            description="Average blood glucose levels over the past 2 to 3 months for diabetes monitoring.",
            category="Diabetology",
        )
        test_lft = DiagnosticTest(
            id=uuid.uuid4(),
            name="Liver Function Test (LFT)",
            description="Assesses liver enzymes, bilirubin, and proteins to monitor liver health.",
            category="Biochemistry",
        )
        test_vit = DiagnosticTest(
            id=uuid.uuid4(),
            name="Vitamin D & B12 Vitality",
            description="Detects bone density deficiencies, fatigue causes, and nerve health issues.",
            category="Nutritional Biochemistry",
        )
        session.add_all([test_cbc, test_lipid, test_thyroid, test_hba1c, test_lft, test_vit])
        await session.flush()

        # 4. Create Centre-Test associations with competitive pricing
        pricing = [
            # Centre 1 - Apollo Mumbai
            CentreTest(centre_id=centre1.id, test_id=test_cbc.id, price=Decimal("450.00")),
            CentreTest(centre_id=centre1.id, test_id=test_lipid.id, price=Decimal("750.00")),
            CentreTest(centre_id=centre1.id, test_id=test_thyroid.id, price=Decimal("600.00")),
            CentreTest(centre_id=centre1.id, test_id=test_hba1c.id, price=Decimal("500.00")),
            CentreTest(centre_id=centre1.id, test_id=test_lft.id, price=Decimal("800.00")),
            CentreTest(centre_id=centre1.id, test_id=test_vit.id, price=Decimal("1400.00")),

            # Centre 2 - Metropolis Delhi
            CentreTest(centre_id=centre2.id, test_id=test_cbc.id, price=Decimal("400.00")),
            CentreTest(centre_id=centre2.id, test_id=test_lipid.id, price=Decimal("700.00")),
            CentreTest(centre_id=centre2.id, test_id=test_thyroid.id, price=Decimal("650.00")),
            CentreTest(centre_id=centre2.id, test_id=test_hba1c.id, price=Decimal("480.00")),
            CentreTest(centre_id=centre2.id, test_id=test_vit.id, price=Decimal("1350.00")),

            # Centre 3 - Dr. Lal PathLabs Bangalore
            CentreTest(centre_id=centre3.id, test_id=test_cbc.id, price=Decimal("420.00")),
            CentreTest(centre_id=centre3.id, test_id=test_lipid.id, price=Decimal("720.00")),
            CentreTest(centre_id=centre3.id, test_id=test_thyroid.id, price=Decimal("590.00")),
            CentreTest(centre_id=centre3.id, test_id=test_lft.id, price=Decimal("780.00")),
            CentreTest(centre_id=centre3.id, test_id=test_vit.id, price=Decimal("1300.00")),
        ]
        session.add_all(pricing)
        await session.commit()

        logger.info("Database seeding complete!")
        return {
            "status": "seeded",
            "message": "Demo data successfully loaded.",
            "demo_accounts": {
                "patient": {"email": "patient@evehealthcare.com", "password": "PatientPass123!"},
                "admin": {"email": "admin@evehealthcare.com", "password": "AdminPass123!"},
            },
            "centres_count": 3,
            "tests_count": 6,
        }


if __name__ == "__main__":
    res = asyncio.run(seed_data())
    print(res)
