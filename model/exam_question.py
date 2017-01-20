from __future__ import absolute_import, with_statement, print_function
from sqlalchemy import Column, String
from sqlalchemy.dialects.mysql import INTEGER

from .base import Base

class ExamQuestion(Base):
  __tablename__ = 'exam_question'
  exam_id = Column(INTEGER(unsigned=True))
  question_id = Column(INTEGER(unsigned=True))
  info = Column(String(length=1000))
