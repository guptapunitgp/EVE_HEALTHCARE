"""Insert minimal Bengaluru demo catalogue records without overwriting existing data."""
import argparse
from decimal import Decimal
from pathlib import Path
import sys

# Keep `python scripts/seed_demo.py` working in both local and container runs.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest


CENTRES = [
    {
        "name": "Sunrise Diagnostics",
        "address": "18, 100 Feet Road, Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "phone": "+91-80000-10001",
        "description": "Sample centre for local development and product walkthroughs.",
        "services": ["Pathology", "Blood Tests", "X-Ray"],
    },
    {
        "name": "HealthSure Diagnostic Centre",
        "address": "42, 80 Feet Road, Koramangala",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560034",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "phone": "+91-80000-10002",
        "description": "Sample centre for local development and product walkthroughs.",
        "services": ["Pathology", "Ultrasound", "ECG"],
    },
    {
        "name": "Care & Cure Diagnostics",
        "address": "7, Bannerghatta Road, Jayanagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560041",
        "latitude": 12.9250,
        "longitude": 77.5938,
        "phone": "+91-80000-10003",
        "description": "Sample centre for local development and product walkthroughs.",
        "services": ["Pathology", "Radiology", "Full Body Checkup"],
    },
]

TESTS = [
    ("Complete Blood Count (CBC)", "Pathology", "Blood", Decimal("499.00"), 30, 360),
    ("Lipid Profile", "Pathology", "Blood", Decimal("799.00"), 30, 720),
    ("Thyroid Profile", "Pathology", "Blood", Decimal("699.00"), 30, 720),
    ("Vitamin D", "Pathology", "Blood", Decimal("999.00"), 30, 1440),
    ("Fasting Blood Sugar", "Pathology", "Blood", Decimal("199.00"), 15, 180),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-demo-data", action="store_true", help="explicitly allow inserting sample records")
    args = parser.parse_args()
    if not args.confirm_demo_data:
        parser.error("pass --confirm-demo-data to insert sample records")
    if settings.ENVIRONMENT.lower() != "development":
        parser.error("demo data can only be seeded when ENVIRONMENT=development")

    with SessionLocal.begin() as db:
        centres = {}
        for payload in CENTRES:
            centre = db.scalar(select(DiagnosticCentre).where(DiagnosticCentre.name == payload["name"]))
            if centre is None:
                centre = DiagnosticCentre(**payload)
                db.add(centre)
                db.flush()
            centres[centre.name] = centre

        tests = {}
        for name, category, sample, price, duration, report_minutes in TESTS:
            test = db.scalar(select(DiagnosticTest).where(DiagnosticTest.name == name))
            if test is None:
                test = DiagnosticTest(
                    name=name,
                    category=category,
                    sample_type=sample,
                    description=f"{name} diagnostic test.",
                    preparation_instructions="Follow any instructions provided by your clinician.",
                    duration_minutes=duration,
                    estimated_report_time_minutes=report_minutes,
                )
                db.add(test)
                db.flush()
            tests[name] = (test, price)

        for centre_index, centre in enumerate(centres.values()):
            for test_index, (test, price) in enumerate(tests.values()):
                existing = db.scalar(
                    select(CentreTest).where(
                        CentreTest.centre_id == centre.id,
                        CentreTest.test_id == test.id,
                    )
                )
                if existing is None:
                    db.add(CentreTest(
                        centre_id=centre.id,
                        test_id=test.id,
                        price=price + Decimal(centre_index * 25 + test_index * 10),
                        is_available=True,
                    ))
    print("Demo centre, test, and offering records are present. Existing records were left unchanged.")


if __name__ == "__main__":
    main()
