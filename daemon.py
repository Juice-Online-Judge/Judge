from __future__ import absolute_import, with_statement, print_function
import socket
import os
from os import path
import json
import re
import time

from dotenv import load_dotenv

from sqlalchemy.orm import contains_eager
from model import create_session, session_scope, Judge, Submission, ExamQuestion
from container import container, build_container
from utils import timestamp

DOTENV_PATH = path.join(path.dirname(__file__), '.env')
load_dotenv(DOTENV_PATH)

create_session(
  host=os.environ.get('DB_HOST'),
  username=os.environ.get('DB_USERNAME'),
  password=os.environ.get('DB_PASSWORD'),
  database=os.environ.get('DB_DATABASE')
)

WHITE_FUNC = [
  'stdio.h',
  'stdlib.h',
  'string.h',
  'ctype.h',
  'time.h',
  'stdbool.h',
  'unistd.h',
  'math.h'
]
BLACK_FUNC = ['system']

def save_judge_result(judge_result):
  with session_scope() as session:
    session.add(judge_result)

def retrieve():
  with session_scope() as session:
    summit = session.query(
      Submission.id,
      Submission.question_id,
      Submission.exam_id,
      Submission.code
    ).outerjoin(Judge).join(Submission.question).options(
      contains_eager(Submission.question)
    ).filter(Judge.submission_id == None).all()

  # retrieve all results
  if not summit:
    rest_time = timestamp()
    print(rest_time, 'Judge rests. All done!')
    return

  for submission in summit:
    # initial judge in docker

    judge_result = judge(submission)
    save_judge_result(judge_result)

def judge(submission):
  sid = submission.id
  qid = submission.question_id
  eid = submission.exam_id
  code_path = submission.code

  if filter_header(code_path):
    end_time = timestamp()
    print('{0} Judge Finished: submission_id={1}, result=RF, correctness=0'.format(end_time, sid))
    judge_result = Judge(
      submission_id=sid,
      result='RE',
      correctness=0,
      judge_message='N/A',
      time=0
    )
    return judge_result

  info = json.loads(submission.question.judge)
  result = container(
    sid,
    code_path,
    info['input'],
    info['output'],
    info['restriction']['time'],
    info['restriction']['memory']
  )
  # retrieve exam info
  if eid is not None:
    with session_scope() as session:
      exam_question = session.query(ExamQuestion.info).filter(
        ExamQuestion.exam_id == eid,
        ExamQuestion.question_id == qid
      ).first()
    info = json.loads(exam_question.info)

  correctness = 0
  judge_msg = 'N/A'
  if result['ac_count'] == result['outcount']:
    end_result = 'AC'
    correctness = 100
  else:
    end_result = result['wrong_result']
    if eid and info['type'] == 'proportion':
      correctness = int(result['ac_count']) * 100 // result['outcount']
      if result['ac_count'] > 0:
        end_result = 'PC'
  # insert to TABLE judge
  end_time = timestamp()
  print('{0} Judge Finished: submission_id={1}, result={2}, correctness={3}'.format(
    end_time,
    sid,
    end_result,
    correctness
  ))
  judge_result = Judge(
    submission_id=sid,
    result=end_result,
    correctness=correctness,
    judge_message=judge_msg,
    time=round(result['max_time'], 3)
  )
  ini_time = timestamp()
  print(ini_time, 'Judge Initiate: sumission_id =', sid)
  return judge_result

def filter_header(code_path):
  # retrieve result one by one
  header = r'[a-z|A-Z|/|0-9]*[.]h'
  with open(code_path, 'r') as code:
    pats = re.findall(header, code.read())
    for pat in pats:
      if not pat in WHITE_FUNC:
        return True

    #function = '[a-z|A-Z|0-9|\_][\(]*[\)]'
    for black in BLACK_FUNC:
      if not code.read().find(black) == -1:
        print(code.read())
        return True
  return False

def main():
  import pwd
  import grp
  base_path = os.path.dirname(os.path.realpath(__file__))
  build_container(base_path)
  # First run
  start_time = timestamp()
  print(start_time, ' Daemon Starts. Your order is my command!')

  retrieve()

  # Socket
  if not os.path.exists('/var/run/judge'):
    os.mkdir('/var/run/judge')
  server_addr = '/var/run/judge/judge.sock'

  # Make sure the socket does not already exist
  try:
    os.unlink(server_addr)
  except OSError:
    if os.path.exists(server_addr):
      raise

  # Create socket
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

  # Bind the socket to the port
  sock.bind(server_addr)

  # Grant www-data access
  uid = pwd.getpwnam('www-data').pw_uid
  gid = grp.getgrnam('www-data').gr_gid
  os.chown(server_addr, uid, gid)

  # Listen for incoming connections
  sock.listen(1)

  # Daemon
  while True:
    connection, _ = sock.accept()
    try:
      msg = connection.recv(16)
      if msg:
        time.sleep(1)
        retrieve()

    finally:
      # Clean up the connection
      connection.close()

if __name__ == '__main__':
  main()
