# Внешние зависимости
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession
import sqlalchemy.orm as so
import sqlalchemy as sa


class Base(AsyncAttrs, so.DeclarativeBase):
    def update_from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
        

organization_activity = sa.Table(
    "organization_activity",
    Base.metadata,
    sa.Column("organization_id", sa.ForeignKey("organizations.id"), primary_key=True),
    sa.Column("activity_id", sa.ForeignKey("activities.id"), primary_key=True)
)


# Модель Здания
class Building(Base):
    __tablename__ = "buildings"
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    address: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True, index=True, nullable=False)
    latitude: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    longitude: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    
    connect_organization: so.Mapped[List["Organization"]] = so.relationship(
        "Organization",
        back_populates="connect_building"
    )
    
    
# Модель Организации
class Organization(Base):
    __tablename__ = "organizations"
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, index=True, nullable=False)
    building_id: so.Mapped[int] = so.mapped_column(
        sa.Integer,
        sa.ForeignKey('buildings.id'),
        index=True,
        nullable=False
    )
    
    connect_building: so.Mapped["Building"] = so.relationship(
        "Building", 
        back_populates="connect_organization"
    )
    
    connect_activities: so.Mapped[List["Activity"]] = so.relationship(
        "Activity",
        secondary=organization_activity,
        back_populates="connect_organizations"
    )
    
    connect_numbers: so.Mapped[List["PhoneNumber"]] = so.relationship(
        "PhoneNumber",
        back_populates="connect_organizations"
    )
    

# Модель Деятельности
class Activity(Base):
    __tablename__ = "activities"
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True, index=True, nullable=False)
    parent_id: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, sa.ForeignKey("activities.id"), index=True, nullable=True)
    
    children: so.Mapped[Optional[List["Activity"]]] = so.relationship(
        "Activity",
        back_populates="parent"
    )
    
    parent: so.Mapped[Optional["Activity"]] = so.relationship(
        "Activity",
        remote_side=[id],
        back_populates="children"
    )
    
    connect_organizations: so.Mapped[List["Organization"]] = so.relationship(
        "Organization",
        secondary=organization_activity,
        back_populates="connect_activities"
    )
    
    
# Модель Номеров Телефона
class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    number: so.Mapped[str] = so.mapped_column(sa.String(20), unique=True, index=True, nullable=False)
    organization_id: so.Mapped[int] = so.mapped_column(
        sa.Integer, 
        sa.ForeignKey("organizations.id"),
        index=True,
        nullable=False
    )
    
    connect_organizations: so.Mapped["Organization"] = so.relationship(
        "Organization",
        back_populates="connect_numbers"
    )