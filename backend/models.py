from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class API(Base):
    __tablename__ = "apis"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    active = Column(Boolean, default=True)


class MonitoringCheck(Base):
    __tablename__ = "monitoring_checks"

    id = Column(Integer, primary_key=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False)
    status = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time = Column(Float)
    error = Column(Text)
    checked_at = Column(DateTime, default=datetime.utcnow)