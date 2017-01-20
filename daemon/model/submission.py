from __future__ import absolute_import, with_statement, print_function
from sqlalchemy import Column, String, TIMESTAMP
from sqlalchemy.dialects.mysql import INTEGER

from .base import Base

class Submission(Base):
  __tablename__ = 'submissions'
  id = Column(INTEGER(unsigned=True), primary_key=True)
  user_id = Column(INTEGER(unsigned=True))
  question_id = Column(INTEGER(unsigned=True))
  exam_id = Column(INTEGER(unsigned=True))
  language = Column(String(length=16))
  code = Column(String(length=190))
  submitted_at = Column(TIMESTAMP(), nullable=True)

