from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class LaboDB(Base):
    __tablename__ = "labos"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, index=True)
    analyses = relationship("AnalyseDB", back_populates="labo")
    utilisateurs = relationship("UserDB", back_populates="labo")

class AnalyseDB(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    type_analyse = Column(String)
    statut = Column(String, default="en_attente")
    message = Column(String, default="")
    labo_id = Column(Integer, ForeignKey("labos.id"))
    labo = relationship("LaboDB", back_populates="analyses")

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    labo_id = Column(Integer, ForeignKey("labos.id"))
    labo = relationship("LaboDB", back_populates="utilisateurs")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)