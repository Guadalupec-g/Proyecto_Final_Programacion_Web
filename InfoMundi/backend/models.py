from sqlalchemy import Column, Integer, String
from .database import Base


class Favorito(Base):
    __tablename__ = "favorito"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100))
    comentario = Column(String(255))
    imagen_url = Column(String(255))
