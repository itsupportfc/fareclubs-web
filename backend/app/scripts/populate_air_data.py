# app/scripts/populate_air_data.py
import asyncio
import os
import pandas as pd
from sqlalchemy import select, func

from app.db.database import AsyncSessionLocal
from app.db.models.air_data import Airline, Airport

# ✅ Extensions supported
LOGO_EXTENSIONS = [".png", ".gif", ".jpg", ".jpeg", ".bmp"]


def find_logo_for_code(code: str, static_dir: str = "static/logos") -> str | None:
    """Return /static/logos/{code}.{ext} if file exists."""
    code = code.strip()
    for ext in LOGO_EXTENSIONS:
        for name_variant in [code, code.lower(), code.upper()]:
            path = os.path.join(static_dir, f"{name_variant}{ext}")
            if os.path.exists(path):
                return f"/static/logos/{name_variant}{ext}"
    return None


async def populate_air_data():
    async with AsyncSessionLocal() as session:
        # Skip if data already populated
        result = await session.execute(select(func.count()).select_from(Airline))
        if result.scalar() > 0:
            print("✅ Air data already populated, skipping.")
            return

        # --- Load airlines ---
        airlines_path = os.path.join("data", "Airline Code.xlsx")
        if not os.path.exists(airlines_path):
            raise FileNotFoundError(f"{airlines_path} not found")

        airlines_df = pd.read_excel(airlines_path)
        for _, row in airlines_df.iterrows():
            code = str(row["AIRLINECODE"]).strip().upper()
            name = str(row["AIRLINENAME"]).strip()
            logo_url = find_logo_for_code(code)

            result = await session.execute(select(Airline).where(Airline.code == code))
            airline = result.scalar_one_or_none()
            if not airline:
                session.add(Airline(code=code, name=name, logo_url=logo_url))
            else:
                # update if missing logo or different
                if logo_url and airline.logo_url != logo_url:
                    airline.logo_url = logo_url
                    session.add(airline)

        # --- Load airports ---
        airports_path = os.path.join("data", "updated Airport 1.csv")
        if not os.path.exists(airports_path):
            raise FileNotFoundError(f"{airports_path} not found")

        airports_df = pd.read_csv(airports_path, on_bad_lines="skip")
        for _, row in airports_df.iterrows():
            airport_code = str(row["AIRPORTCODE"]).strip().upper()
            result = await session.execute(
                select(Airport).where(Airport.airport_code == airport_code)
            )
            if not result.scalar_one_or_none():
                session.add(
                    Airport(
                        city_name=str(row["CITYNAME"]).strip(),
                        city_code=str(row["CITYCODE"]).strip(),
                        country_code=str(row["COUNTRYCODE"]).strip(),
                        country_name=str(row["COUNTRYNAME"]).strip(),
                        airport_code=airport_code,
                        airport_name=str(row["AIRPORTNAME"]).strip(),
                    )
                )

        await session.commit()
        print("✅ Airlines & airports populated successfully.")


if __name__ == "__main__":
    asyncio.run(populate_air_data())

