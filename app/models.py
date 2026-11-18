from sqlalchemy import Column, Integer, String
from .database import Base

class AnalyseDB(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    type_analyse = Column(String)
    statut = Column(String, default="en_attente")
    message = Column(String, default="")