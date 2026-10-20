import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime

# Подключение к базе данных из переменной окружения DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Обработка префикса URL для совместимости со SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель таблицы Каизен-предложений
class KaizenProposalModel(Base):
    __tablename__ = "kaizen_proposals"

    id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String(255), nullable=False)
    author_id = Column(String(100), nullable=True)
    department = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    status = Column(String(50), default="на рассмотрении")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kaizen Mebelain API")

# Разрешаем CORS-запросы с вашего фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic схемы
class KaizenCreate(BaseModel):
    author_name: str
    author_id: str | None = None
    department: str
    title: str
    problem: str
    solution: str

class KaizenResponse(KaizenCreate):
    id: int
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/kaizens", response_model=List[KaizenResponse])
def get_kaizens(db: Session = Depends(get_db)):
    return db.query(KaizenProposalModel).order_by(KaizenProposalModel.created_at.desc()).all()

@app.post("/api/kaizens", response_model=KaizenResponse)
def create_kaizen(proposal: KaizenCreate, db: Session = Depends(get_db)):
    db_item = KaizenProposalModel(**proposal.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
