
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.collections import column_mapped_collection

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Unicode, DateTime, LargeBinary, ForeignKey

from datetime import datetime

Session = sessionmaker()
Base = declarative_base()


class KeyValuePair(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    blob = Column(ForeignKey('blobs.id'), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Unicode, nullable=False)


class Blob(Base):
    __tablename__ = 'blobs'

    id = Column(String(36), primary_key=True)

    tags = relationship('KeyValuePair', cascade='all, delete-orphan')

    created = Column(DateTime, default=datetime.now)
    timeout = Column(DateTime, nullable=True)

    type = Column(String(), default='application/octet-stream')
    data = Column(LargeBinary(), nullable=False)


def init(uri):
    engine = create_engine(uri)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
