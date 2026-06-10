from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

db_url = settings.DATABASE_URL
# Supabase direct connection is IPv6 only, which fails on IPv4-only networks.
# We redirect to the Supabase Connection Pooler (which supports IPv4) and use the pg8000 driver.
if "db.uoplbhmayrlgarktdkve.supabase.co" in db_url:
    db_url = db_url.replace("db.uoplbhmayrlgarktdkve.supabase.co:5432", "aws-1-ap-northeast-1.pooler.supabase.com:6543")
    if db_url.startswith("postgresql://postgres:"):
        db_url = db_url.replace("postgresql://postgres:", "postgresql+pg8000://postgres.uoplbhmayrlgarktdkve:", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

engine = create_engine(db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
