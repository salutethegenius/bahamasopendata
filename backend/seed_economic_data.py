"""
Seed script for economic indicators data.
Run this script to populate the database with initial income/cost of living data.

Usage:
    python -m backend.seed_economic_data
"""
import asyncio
from datetime import date
from sqlalchemy import select
from app.db.database import AsyncSessionLocal, engine
from app.db.models import Base, EconomicIndicator


async def seed_economic_data():
    """Seed the database with economic indicator data from the 2024 study."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if data already exists
            result = await session.execute(select(EconomicIndicator))
            existing = result.scalars().first()
            
            if existing:
                print("Economic indicator data already exists. Skipping seed.")
                return
            
            # Data from the 2024 University of The Bahamas study
            indicators = [
                # New Providence - Middle Class
                EconomicIndicator(
                    indicator_type="middle_class",
                    island="new_providence",
                    year=2024,
                    month_amount=10200.0,
                    annual_amount=122400.0,
                    breakdown={
                        "food": 2500.0,
                        "housing_utilities": 2142.0,
                        "nfnh": 3508.0,
                        "savings": 2040.0
                    },
                    source_document="How Much Does It Cost to Be Middle Class in The Bahamas?",
                    source_url="https://www.ub.edu.bs/wp-content/uploads/Archer2024Final.pdf",
                    author="Lesvie Archer",
                    published_date=date(2024, 3, 1)
                ),
                # New Providence - Working Class
                EconomicIndicator(
                    indicator_type="working_class",
                    island="new_providence",
                    year=2024,
                    month_amount=5000.0,
                    annual_amount=60000.0,
                    breakdown=None,
                    source_document="The Bahamas Living Wages Survey (updated to 2024)",
                    source_url="https://www.ub.edu.bs/wp-content/uploads/2016/10/GPPI_Living-Wage-Survey_revised_27-May-2021.pdf",
                    author="Lesvie Archer et al.",
                    published_date=date(2020, 3, 1)
                ),
                # Grand Bahama - Middle Class
                EconomicIndicator(
                    indicator_type="middle_class",
                    island="grand_bahama",
                    year=2024,
                    month_amount=10100.0,
                    annual_amount=121200.0,
                    breakdown={
                        "food": 2850.0,
                        "housing_utilities": 1692.0,
                        "nfnh": 3508.0,
                        "savings": 2020.0
                    },
                    source_document="How Much Does It Cost to Be Middle Class in The Bahamas?",
                    source_url="https://www.ub.edu.bs/wp-content/uploads/Archer2024Final.pdf",
                    author="Lesvie Archer",
                    published_date=date(2024, 3, 1)
                ),
                # Grand Bahama - Working Class
                EconomicIndicator(
                    indicator_type="working_class",
                    island="grand_bahama",
                    year=2024,
                    month_amount=6600.0,
                    annual_amount=79200.0,
                    breakdown=None,
                    source_document="The Bahamas Living Wages Survey (updated to 2024)",
                    source_url="https://www.ub.edu.bs/wp-content/uploads/2016/10/GPPI_Living-Wage-Survey_revised_27-May-2021.pdf",
                    author="Lesvie Archer et al.",
                    published_date=date(2020, 3, 1)
                ),
            ]
            
            for indicator in indicators:
                session.add(indicator)
            
            await session.commit()
            print(f"✅ Successfully seeded {len(indicators)} economic indicators")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding data: {e}")
            raise


async def main():
    """Main entry point."""
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_economic_data()


if __name__ == "__main__":
    asyncio.run(main())
