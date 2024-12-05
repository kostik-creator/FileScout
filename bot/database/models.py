from sqlalchemy import DateTime, Integer, String, Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class Group(Base):
    __tablename__ = 'groups'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)

    users = relationship("User", back_populates="group")

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'), nullable=False)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    group = relationship("Group", back_populates="users")

class Admin(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)     

    password: Mapped[str] = mapped_column(Text, nullable=False)
