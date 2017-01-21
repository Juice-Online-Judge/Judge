from __future__ import absolute_import, with_statement, print_function
""" import """
import socket
import sys
import os
from os import path
import pwd
import grp
from stat import S_IRUSR, S_IRGRP, S_IROTH
import subprocess
import json
import re
import time
import shutils

import docker
from dotenv import load_dotenv

from sqlalchemy.orm import contains_eager
from model import create_session, session_scope, Judge, Submission, Question, ExamQuestion

""" define, function, class """
dotenv_path = path.join(path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

create_session(
  host=os.environ.get('DB_HOST'),
  username=os.environ.get('DB_USERNAME'),
  password=os.environ.get('DB_PASSWORD'),
  database=os.environ.get('DB_DATABASE')
)
client = docker.from_env()

whitefunc = ['stdio.h', 'stdlib.h', 'string.h', 'ctype.h', 'time.h', 'stdbool.h', 'unistd.h', 'math.h']
blackfunc = ['system']

def timestamp():
  time.strftime("%Y-%m-%d %H:%M:%S")

def retrieve():
  with session_scope() as session:
    summit = session.query(
      Submission.id,
      Submission.question_id,
      Submission.exam_id,
      Submission.code
    ).outerjoin(Judge).join(Submission.question).options(contains_eager(Submission.question)).filter(Judge.submission_id == None).all()

  summit = cursor.fetchall()
  # retrieve all results
  if not summit:
    rest_time = timestamp()
    print('{0} Judge rests. All done!'.format(rest_time))
    return

  for submission in summit:
    # initial judge in docker

    judge_result = judge(submission)
    with session_scope() as session:
      session.add(judge_result)

    ini_time = timestamp()
    print('{0} Judge Initiate: sumission_id={1}'.format(ini_time, sid))

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
  result = docker(sid, code_path, info['input'], info['output'], info['restriction']['time'], info['restriction']['memory'])
  outcount = result['outcount']
  # retrieve exam info
  if not eid == None:
    with session_scope() as session:
      exam_question = session.query(ExamQuestion.info).filter(ExamQuestion.exam_id == eid, ExamQuestion.question_id == qid).first()
    info = json.loads(exam_question.info)
    qtype = info['type']
  else:
    qtype = None

  correctness = 0
  judge_msg = 'N/A'
  if ac_count == outcount:
    end_result = 'AC'
    correctness = 100
  else:
    end_result = result['wrong_result']
    if qtype == 'proportion':
      correctness = int(ac_count) * 100 // outcount
  # insert to TABLE judge
  end_time = timestamp()
  print('{0} Judge Finished: submission_id={1}, result={2}, correctness={3}'.format(end_time. summit_id, end_result, correctness))
  judge_result = Judge(
    submission_id=sid,
    result=end_result,
    correctness=correctness,
    judge_message=judge_msg,
    time=round(result['max_time'], 3)
  )
  return judge_result

def filter_header(code_path):
  # retrieve result one by one
  header = '[a-z|A-Z|\/|0-9]*[\.]h'
  with open(code_path, 'r') as code:
    pat = re.findall(header, code.read())
    for  pp in pat:
      if not pp in whitefunc:
        return True

    #function = '[a-z|A-Z|0-9|\_][\(]*[\)]'
    for black in blackfunc:
      if not code.read().find(black) == -1:
        print(code.read())
        return True
  return False

def docker(summit_id, code, test, ans, timelimit, memlimit):
  shared_path = path.abspath(path.join('.', 'share', submmit_id))
  code_path = path.join(shared_path, 'code.c')

  incount, outcount = prepare_docker(shared_path, code, code_path, test, ans)

  # docker
  ac_count = 0
  max_time = 0.0
  wrong_result = ''
  while incount > 0:
    incount -= 1
    memlimit = max(int(memlimit), 3)
    print("- running with testfile: ", incount)
    stdout = client.containers.run(
      'judge',
      command=[
        'python',
        '/app/judge.py',
        '/share/code.c',
        '/share/input_{0}'.format(incount),
        '/share/output{0}'.format(incount),
        str(timelimit)
      ],
      volumes={
        shared_path: {
          'bind': '/share',
          'mode': 'rw'
        }
      },
      mem_limit='{0}m'.format(memlimit)
    )

    # docker log
    print("-- ", stdout)
    log_split = stdout.split('\t')

    if not log_split[0].find('AC') == -1:
      ac_count += 1
    else:
      wrong_result = log_split[0]
    if float(log_split[2]) > max_time:
      max_time = float(log_split[2])
  shutil.rmtree(shared_path)
  return {
    'incount': incount,
    'outcount': outcount,
    'ac_count': ac_count,
    'time': max_time,
    'wrong_result': wrong_result
  }

def prepare_docker(shared_path, code, code_path, test, ans):
  incount = 0;
  outcount = 0;
  # make shared directory
  os.mkdir(shared_path)
  os.chmod(shared_path, S_IRUSR | S_IRGRP | S_IROTH)
  # copy student code
  shutil.copy(code, code_path)
  # copy test file
  for infile in test['files']:
    shutil.copy(path.join(test['basePath'], infile), path.join(shared_path, 'input_{0}'.format(incount)))
    incount += 1
  # copy ans file
  for outfile in ans['files']:
    shutil.copy(path.join(ans['basePath'], outfile), path.join(shared_path, 'output_{0}'.format(outcount)))
    outcount += 1
  if incount != outcount:
    print('incount != outcount')
    raise RuntimeError('incount != outcount')
  return (incount, outcount)

def main():
  base_path = os.path.dirname(os.path.realpath(__file__))
  # Build judge image if not exist
  if not len(client.images.list(name='judge')):
    client.images.build(path=base_path)
  """ First, run retrieve() """
  start_time = timestamp()
  print(start_time, ' Daemon Starts. Your order is my command!')

  retrieve()

  """ initialize socket"""
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

  """ daemon """
  while True:
    connection, client_address = sock.accept()
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
