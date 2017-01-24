from __future__ import absolute_import, with_statement, print_function
from contextlib import contextmanager
from future.utils import with_metaclass
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.engine.url import URL
from .singleton import Singleton

class SessionManager(with_metaclass(Singleton)):
  def __init__(self):
    self.session = None

  def get(self):
    return self.session

  def exist(self):
    return self.session is not None

  def set(self, session):
    self.session = session

def create_session(**kargs):
  manager = SessionManager()
  if manager.exist():
    return manager.get()
  url = str(URL('mysql', **kargs))
  engine = create_engine(url)
  session = Session(bind=engine)
  manager.set(session)
  return session

@contextmanager
def session_scope():
  manager = SessionManager()
  if not manager.exist():
    raise RuntimeError('Session not exist')
  session = manager.get()
  try:
    yield session
    session.commit()
  except:
    session.rollback()
    raise
