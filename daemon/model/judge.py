from __future__ import absolute_import, with_statement, print_function
from sqlalchemy import Column, String, ForeignKey, Numeric, TIMESTAMP
from sqlalchemy.dialects.mysql import TINYINT, INTEGER
from sqlalchemy.orm import relationship

from .base import Base
from .submission import Submission

class Judge(Base):
  __tablename__ = 'judges'
  id = Column(INTEGER(unsigned=True), primary_key=True)
  submission_id = Column(INTEGER(unsigned=True), ForeignKey('submissions.id'))
  result = Column(String(length=5))
  correctness = Column(TINYINT(unsigned=True), default=0)
  score = Column(Numeric(precision=6, scale=3), nullable=True)
  judge_message = Column(String(length=5000), nullable=True)
  time = Column(Numeric(precision=6, scale=3), nullable=True)
  memory = Column(Numeric(precision=6, scale=3), nullable=True)
  file = Column(TINYINT(unsigned=True), default=0)
  judged_at = Column(TIMESTAMP(), nullable=True)

  submission = relationship('Submission')

