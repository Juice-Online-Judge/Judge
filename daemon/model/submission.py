from __future__ import absolute_import, with_statement, print_function
from sqlalchemy import Column, Integer, String, TIMESTAMP

from .base import Base

class Submission(Base):
  __tablename__ = 'submissions'
  id = Column(Integer(unsigned=True), primary_key=True)
  user_id = Column(Integer(unsigned=True))
  question_id = Column(Integer(unsigned=True))
  exam_id = Column(Integer(unsigned=True))
  language = Column(String(length=16))
  code = Column(String(length=190))
  submitted_at = Column(TIMESTAMP(), nullable=True)

