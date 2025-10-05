"""
GPT Findability Tracker

This tiny FastAPI app just proves it's alive and listening.
More brains coming later... for now, it's a friendly healthcheck.
"""

__version__ = "0.1.0"

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional, Generator
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Float,
    JSON,
    ForeignKey,
    create_engine,
    func,
    event,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker, relationship


app = FastAPI(
    title="GPT Findability Tracker",
    description=(
        f"A tiny heartbeat service to say we're alive. No fluff, just ok. (v{__version__})"
    ),
)


@app.middleware("http")
async def add_version_header(request, call_next):
    response = await call_next(request)
    response.headers["x-app-version"] = __version__
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- tiny SQLite setup (no migrations, just vibes) ---
DATABASE_URL = "sqlite:///./gpt_findability.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite being SQLite
)

# Turn on SQLite foreign keys so cascade actually works
@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
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

    # Keep a handy backref to evaluations (lazy selectin keeps things snappy)
    evaluations = relationship(
        "Evaluation",
        back_populates="company",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score = Column(Float, nullable=False)
    badge = Column(String, nullable=False)  # "excellent"|"good"|"fair"|"poor"
    # yes, this could have been JSON only, but we’re being grown-ups.
    evidence = Column(JSON, nullable=False)  # list[str]
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    company = relationship("Company", back_populates="evaluations")


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
            raise ValueError("Name's a bit short... please use at least 2 characters.")
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
            raise ValueError("Name's a bit short... please use at least 2 characters.")
        return value


class EvaluationOut(BaseModel):
    id: int
    company_id: int
    score: float
    badge: str
    evidence: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Pure scoring helper: no AI, no network ---
SIGNALS: List[str] = [
    "contact page",
    "clear services page",
    "maps/GMB listing",
    "recent updates",
    "reviews/testimonials",
    "online booking/form",
    "basic schema markup",
    "NAP consistent",
    "loads fast",
    "content matches intent",
]


def compute_findability(signals: dict[str, bool]) -> dict:
    """Turn simple boolean hints into a score, badge, and evidence.

    Why this exists: we want something deterministic and explainable
    can read it without guessing hidden magic.
    """
    # Gather which signals are present, preserving our fixed order for sanity
    present_flags = [bool(signals.get(name, False)) for name in SIGNALS]
    n_true = sum(1 for flag in present_flags if flag)

    mentioned = n_true >= 2
    presence = 1.0 if mentioned else 0.0

    if n_true >= 6:
        rank_component = 1.0
    elif n_true >= 4:
        rank_component = 0.9
    elif n_true >= 2:
        rank_component = 0.8
    else:
        rank_component = 0.0

    rank_confidence = min(1.0, 0.3 + 0.1 * n_true)

    overall = 0.6 * presence + 0.3 * rank_component + 0.1 * rank_confidence
    # Clamp for safety because float math can be spicy
    overall = max(0.0, min(1.0, overall))

    if overall >= 0.8:
        badge = "excellent"
    elif overall >= 0.6:
        badge = "good"
    elif overall >= 0.4:
        badge = "fair"
    else:
        badge = "poor"

    evidence_list = [f"+ {name}" for name, flag in zip(SIGNALS, present_flags) if flag]
    if not evidence_list:
        evidence_list = ["No clear signals provided"]

    # yes, this could have been JSON only, but we’re being grown-ups.
    return {"score": overall, "badge": badge, "evidence": evidence_list}


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
                "message": f"No company with id {id} yet... try creating one first.",
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
                "message": f"No company with id {id} yet... try creating one first.",
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
                "message": f"No company with id {id} yet... try creating one first.",
            },
        )
    db.delete(company)
    db.commit()
    # 204 No Content... nothing to return and that's okay


# --- Evaluate endpoint (turn booleans into a persisted Evaluation) ---
class EvaluateIn(BaseModel):
    company_id: int
    has_contact_page: bool
    has_clear_services_page: bool
    has_gmb_or_maps_listing: bool
    has_recent_updates: bool
    has_reviews_or_testimonials: bool
    has_online_booking_or_form: bool
    uses_basic_schema_markup: bool
    has_consistent_name_address_phone: bool
    has_fast_load_time_claim: bool
    content_matches_intent: bool


@app.post("/evaluate", response_model=EvaluationOut, status_code=201)
def evaluate_company(payload: EvaluateIn, db: Session = Depends(get_db)) -> EvaluationOut:
    # First, make sure we're scoring a real company
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "company_not_found",
                "message": f"No company with id {payload.company_id} yet... try creating one first.",
            },
        )

    # Map inputs to our fixed signal names so the scoring stays predictable
    signals = {
        "contact page": payload.has_contact_page,
        "clear services page": payload.has_clear_services_page,
        "maps/GMB listing": payload.has_gmb_or_maps_listing,
        "recent updates": payload.has_recent_updates,
        "reviews/testimonials": payload.has_reviews_or_testimonials,
        "online booking/form": payload.has_online_booking_or_form,
        "basic schema markup": payload.uses_basic_schema_markup,
        "NAP consistent": payload.has_consistent_name_address_phone,
        "loads fast": payload.has_fast_load_time_claim,
        "content matches intent": payload.content_matches_intent,
    }

    # Pure function, pure vibes — no AI, no network calls
    result = compute_findability(signals)

    evaluation = Evaluation(
        company_id=payload.company_id,
        score=float(result["score"]),
        badge=str(result["badge"]),
        evidence=list(result["evidence"]),
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation

