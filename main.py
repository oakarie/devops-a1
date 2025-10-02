"""
GPT Findability Tracker

This tiny FastAPI app just proves it's alive and listening.
More brains coming later... for now, it's a friendly healthcheck.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional, Generator
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import Column, DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import Session, declarative_base, sessionmaker


app = FastAPI(
    title="GPT Findability Tracker",
    description=(
        "A tiny heartbeat service to say we're alive. No fluff, just ok."
    ),
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- tiny SQLite setup (no migrations, just vibes) ---
DATABASE_URL = "sqlite:///./gpt_findability.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite being SQLite
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    niche = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# Pydantic schemas (input and output shapes)
class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    niche: Optional[str] = None

    # Keep names at least 2 chars so they look like real names
    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if value is None or len(value.strip()) < 2:
            raise ValueError("Name's a bit short — please use at least 2 characters.")
        return value


class CompanyOut(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    niche: Optional[str] = None
    created_at: datetime

    # tell Pydantic it's okay to read from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)


class CompanyUpdate(BaseModel):
    # All optional for PATCH; we only touch what's provided
    name: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None
    niche: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value.strip()) < 2:
            raise ValueError("Name's a bit short — please use at least 2 characters.")
        return value


@app.on_event("startup")
def on_startup() -> None:
    """Create tables on boot. No migrations yet, keeping it breezy."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session per request and clean up after ourselves."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Companies API ---
@app.post("/companies", response_model=CompanyOut, status_code=201)
def create_company(
    payload: CompanyCreate, db: Session = Depends(get_db)
) -> CompanyOut:
    # Keep it simple: hydrate the model straight from the payload
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@app.get("/companies", response_model=List[CompanyOut])
def list_companies(
    q: Optional[str] = Query(default=None, description="Filter by name contains"),
    db: Session = Depends(get_db),
) -> List[CompanyOut]:
    query = db.query(Company)
    if q:
        q_normalized = q.strip().lower()
        if q_normalized:
            query = query.filter(func.lower(Company.name).like(f"%{q_normalized}%"))
    return query.order_by(Company.id.asc()).all()


@app.get("/companies/{id}", response_model=CompanyOut)
def get_company(id: int, db: Session = Depends(get_db)) -> CompanyOut:
    company = db.get(Company, id)
    if not company:
        # Friendly 404: helpful and a little human
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": f"No company with id {id} yet — try creating one first.",
            },
        )
    return company


@app.patch("/companies/{id}", response_model=CompanyOut)
def update_company(
    id: int, payload: CompanyUpdate, db: Session = Depends(get_db)
) -> CompanyOut:
    company = db.get(Company, id)
    if not company:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": f"No company with id {id} yet — try creating one first.",
            },
        )

    # Only change what's explicitly sent; leave the rest alone
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return company  # nothing to do, nothing to change

    # Small, readable loop beats clever one-liners here
    for field_name, field_value in updates.items():
        if field_name in {"id", "created_at"}:
            continue  # keep identity and timestamps untouched
        setattr(company, field_name, field_value)

    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@app.delete("/companies/{id}", status_code=204)
def delete_company(id: int, db: Session = Depends(get_db)) -> None:
    company = db.get(Company, id)
    if not company:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": f"No company with id {id} yet — try creating one first.",
            },
        )
    db.delete(company)
    db.commit()
    # 204 No Content — nothing to return and that's okay

