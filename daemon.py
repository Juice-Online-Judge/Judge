from __future__ import absolute_import, with_statement, print_function
""" import """
import socket
import sys
import os
import pwd
import grp
from stat import S_IRUSR, S_IRGRP, S_IROTH
import subprocess
import json
import re
import time
import shutils

import MySQLdb
import docker

""" define, function, class """

db = MySQLdb.connect(
  os.environ.get('DB_HOST'),
  os.environ.get('DB_USERNAME'),
  os.environ.get('DB_PASSWORD'),
  os.environ.get('DB_DATEBASE'),
  charset='utf8'
)
cursor = db.cursor()

client = docker.from_env()

whitefunc = ['stdio.h', 'stdlib.h', 'string.h', 'ctype.h', 'time.h', 'stdbool.h', 'unistd.h', 'math.h']
blackfunc = ['system']

def timestamp():
  time.strftime("%Y-%m-%d %H:%M:%S")

def retrieve():
  global cursor
  sql = 'SELECT `id`, `question_id`, `exam_id`, `code` FROM `submissions` WHERE `id` NOT IN (SELECT `submission_id` FROM `judges`)'
  try:
    # execute SQL statement
    cursor.execute(sql)
  except MySQLdb.Error as e:
    print('Error B {0}: {1}'.format(e.args[0], e.args[1]))

  summit = cursor.fetchall()
  # retrieve all results
  if not summit:
    rest_time = timestamp()
    print('{0} Judge rests. All done!'.format(rest_time))
    return

  # retrieve result one by one
  for record in summit:
    sid = record[0]
    qid = record[1]
    eid = record[2]
    code_path = record[3]

    # restrict function
    header = '[a-z|A-Z|\/|0-9]*[\.]h'
    code = open(code_path, 'r')
    pat = re.findall(header, code.read())
    for  pp in pat:
      if not pp in whitefunc:
        # insert to TABLE judge
        end_time = timestamp()
        print('{0} Judge Finished: submission_id={1}, result=RF, correctness=0'.format(end_time, sid))
        sql = 'INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ({0},"RF",0,"N/A",0)'.format(sid)
        try:
          cursor.execute(sql)
          db.commit()
        except MySQLdb.Error as e:
          print('Error A {0}: {1}'.format(e.args[0], e.args[1]))
        return

    #function = '[a-z|A-Z|0-9|\_][\(]*[\)]'
    for black in blackfunc:
      if not code.read().find(black) == -1:
        print(code.read())
        end_time = timestamp()
        print('{0} Judge Finished: submission_id={1}, result=RF, correctness=0'.format(end_time, sid))
        sql = 'INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ({0},"RF",0,"N/A",0)'.format(sid)
        try:
          cursor.execute(sql)
          db.commit()
        except MySQLdb.Error as e:
          print('Error A {0}: {1}'.format(e.args[0], e.args[1]))
        return

    # retrieve question info
    sql = "SELECT `id`, `judge` FROM `questions` WHERE `id`='{0}'".format(qid)
    cursor.execute(sql)
    question = cursor.fetchall()
    decodejson =  json.loads(question[0][1])

    # initial judge in docker
    ini_time = timestamp()
    print('{0} Judge Initiate: sumission_id={1}'.format(ini_time, sid))
    docker(sid, code_path, decodejson['input'], decodejson['output'], decodejson['restriction']['time'], decodejson['restriction']['memory'], qid, eid)

def docker(summit_id, code, test, ans, timelimit, memlimit, qid, eid):
  from os import path
  incount = 0;
  outcount = 0;
  shared_path = path.abspath(path.join('.', 'share', submmit_id))
  code_path = path.join(shared_path, 'code.c')
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
    print('error: file count mismatch, stopping!')

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
  # retrieve exam info
  if not eid == None:
    sql = "SELECT `info` FROM `exam_question` WHERE `exam_id`='{0}' and `question_id`='{1}'".format(eid, qid)
    cursor.execute(sql)
    question = cursor.fetchall()
    decodejson = json.loads(question[0][0])
    qtype = decodejson['type']
  else:
    qtype = None
  if qtype == None and ac_count == outcount:
    end_result = 'AC'
    judge_msg = 'N/A'
    correctness = '100'
  elif qtype == None and not ac_count == outcount:
    end_result = wrong_result;
    judge_msg = 'N/A'
    correctness = '0'
  elif qtype == 'proportion' and ac_count == outcount:
    end_result = 'AC'
    judge_msg = 'N/A'
    correctness = '100'
  elif qtype == 'proportion' and ac_count == 0:
    end_result = wrong_result
    judge_msg = 'N/A'
    correctness = '0'
  elif qtype == 'proportion' and not ac_count == outcount:
    end_result = 'PC'
    judge_msg = 'N/A'
    correctness = str(int(ac_count)*100/outcount)
  else:
    end_result = 'N/A'
    judge_msg = 'N/A'
    correctness = '0'
  # insert to TABLE judge
  end_time = timestamp()
  print('{0} Judge Finished: submission_id={1}, result={2}, correctness={3}'.format(end_time. summit_id, end_result, correctness))
  sql = 'INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ({0}, {1}, {2}, {3}, {4})'.format(submit_id, end_result, correctness, judge_msg, round(max_time, 3))
  try:
    cursor.execute(sql)
    db.commit()
  except MySQLdb.Error as e:
    print('Error C {0}: {1}'.format(e.args[0], e.args[1]))

  shutil.rmtree(shared_path)

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
        # Perform SQL query
        time.sleep(1)
        retrieve()

    finally:
      # Clean up the connection
      connection.close()

if __name__ == '__main__':
  main()
