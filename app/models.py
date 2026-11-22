from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class LaboDB(Base):
    __tablename__ = "labos"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    users = relationship("UserDB", back_populates="labo")
    patients = relationship("Patient", back_populates="labo")
    analyses = relationship("AnalyseDB", back_populates="labo")

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    labo_id = Column(Integer, ForeignKey('labos.id'), nullable=False)
    labo = relationship("LaboDB", back_populates="users")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    sexe = Column(String(10), nullable=True)
    telephone = Column(String(20), nullable=True)
    labo_id = Column(Integer, ForeignKey('labos.id'), nullable=False)
    labo = relationship("LaboDB", back_populates="patients")
    analyses = relationship("AnalyseDB", back_populates="patient")
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalyseDB(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    type_analyse = Column(String(100), nullable=False)
    statut = Column(String(50), default="En cours")
    labo_id = Column(Integer, ForeignKey('labos.id'), nullable=False)
    labo = relationship("LaboDB", back_populates="analyses")
    patient = relationship("Patient", back_populates="analyses")
    resultats = relationship("Resultat", back_populates="analyse", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=datetime.utcnow)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Resultat(Base):
    __tablename__ = "resultats"
    id = Column(Integer, primary_key=True, index=True)
    analyse_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    nom_test = Column(String(100), nullable=False)
    valeur = Column(String(50), nullable=False)
    unite = Column(String(20), nullable=True)
    norme_min = Column(String(20), nullable=True)
    norme_max = Column(String(20), nullable=True)
    analyse = relationship("AnalyseDB", back_populates="resultats")