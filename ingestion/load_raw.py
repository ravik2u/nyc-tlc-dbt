import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------- 1. Read connection settings from .env ----------
load_dotenv(override=True)

server = os.getenv("SQL_SERVER")
port = os.getenv("SQL_PORT")
database = os.getenv("SQL_DATABASE")
user = os.getenv("SQL_USER")
password = os.getenv("SQL_PASSWORD")

# ---------- 2. Build the database connection ----------
url = (
    f"mssql+pyodbc://{user}:{password}@{server},{port}/{database}"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)
engine = create_engine(url, fast_executemany=True)


# ---------- 3. Create the raw schema if missing ----------
def create_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("IF SCHEMA_ID('raw') IS NULL EXEC('CREATE SCHEMA raw')"))
    print("Schema 'raw' ready")


# ---------- 4. Load trip parquet files (idempotent per file) ----------
def load_trips(engine):
    files = sorted(Path("data/trips").glob("*.parquet"))
    if not files:
        print("No parquet files found in data/trips")
        return

    for file in files:
        df = pd.read_parquet(file)
        df["_source_file"] = file.name
        df["_loaded_at"] = datetime.now()

        # Delete this file's old rows so a rerun never duplicates data
        with engine.begin() as conn:
            if conn.execute(text("SELECT OBJECT_ID('raw.fhv_trips')")).scalar():
                conn.execute(
                    text("DELETE FROM raw.fhv_trips WHERE _source_file = :f"),
                    {"f": file.name},
                )

        df.to_sql(
            "fhv_trips",
            engine,
            schema="raw",
            if_exists="append",
            index=False,
            chunksize=50000,
        )
        print(f"{file.name}: {len(df):,} rows loaded")


# ---------- 5. Load latest vehicles CSV (full refresh) ----------
def load_vehicles(engine):
    files = sorted(Path("data/vehicles").glob("fhv_vehicles_*.csv"))
    if not files:
        print("No vehicle files found in data/vehicles")
        return

    latest = files[-1]  # newest date in the file name
    df = pd.read_csv(latest, dtype=str)  # keep everything as text in raw

    # Clean column names: "Vehicle License Number" -> "vehicle_license_number"
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    df["_source_file"] = latest.name
    df["_loaded_at"] = datetime.now()

    df.to_sql(
        "fhv_vehicles",
        engine,
        schema="raw",
        if_exists="replace",  # raw always holds the current state
        index=False,
        chunksize=50000,
    )
    print(f"{latest.name}: {len(df):,} rows loaded")


# ---------- 6. Run ----------
if __name__ == "__main__":
    create_schema(engine)
    load_trips(engine)
    load_vehicles(engine)
    print("Done")