from __future__ import absolute_import, with_statement, print_function
from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.dialects.mysql import TINYINT, INTEGER
from sqlalchemy.orm import relationship

from .base import Base

class Question(Base):
  __tablename__ = 'questions'
  id = Column(INTEGER(unsigned=True), primary_key=True)
  uuid = Column(String(length=36))
  user_id = Column(INTEGER(unsigned=True))
  title = Column(String(length=96))
  description = Column(String(length=10000))
  judge = Column(String(length=1500))
  public = Column(TINYINT(), default=0)
  created_at = Column(TIMESTAMP(), nullable=True)
  updated_at = Column(TIMESTAMP(), nullable=True)
  deleted_at = Column(TIMESTAMP(), nullable=True)
