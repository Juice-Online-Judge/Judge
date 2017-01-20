from __future__ import absolute_import, with_statement, print_function
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.engine.url import URL
from .base import Base

session = None

def create_session(**kargs):
  if session is not None:
    return session
  url = str(URL('mysql', **kargs))
  engine = create_engine(url)
  session = Session(bind=engine)
  return session

