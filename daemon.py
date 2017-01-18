from __future__ import absolute_import, with_statement, print_function
""" import """
import socket
import sys
import os
import commands
import MySQLdb
import json
import re
import time
import signal

""" define, function, class """

db = MySQLdb.connect(
  os.environ.get('DB_HOST'),
  os.environ.get('DB_USERNAME'),
  os.environ.get('DB_PASSWORD'),
  os.environ.get('DB_DATEBASE'),
  charset='utf8'
)
cursor = db.cursor()

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
  incount = 0;
  outcount = 0;
  # make shared directory
  status, stdout = commands.getstatusoutput("mkdir share/"+str(summit_id))
  status, stdout = commands.getstatusoutput("chmod 444 share/"+str(summit_id))
  # copy judge.py
  status, stdout = commands.getstatusoutput("cp judge.py share/"+str(summit_id)+"/.")
  # copy student code
  status, stdout = commands.getstatusoutput("cp "+code+" share/"+str(summit_id)+"/code.c")
  # copy test file
  for infile in test['files']:
    status, stdout = commands.getstatusoutput("cp "+test['basePath']+"/"+infile+" share/"+str(summit_id)+"/input_"+str(incount))
    incount += 1
  # copy ans file
  for outfile in ans['files']:
    status, stdout = commands.getstatusoutput("cp "+ans['basePath']+"/"+outfile+" share/"+str(summit_id)+"/output_"+str(outcount))
    outcount += 1

  if incount != outcount:
    print('error: file count mismatch, stopping!')

  # docker
  ac_count = 0
  max_time = 0.0
  wrong_result = ''
  while incount > 0:
    incount -= 1
    if int(memlimit) < 3:
            memlimit = 3
    print("- running with testfile: ", incount)
    arg = "docker run -m "+str(int(memlimit)+1)+"m -v /home/silenttulips/share/"+str(summit_id)+":/share ubuntu:latest /usr/bin/python2.7 /share/judge.py "+str(summit_id)+" /share/code.c /share/input_"+str(incount)+" /share/output_"+str(incount)+" "+str(timelimit)
    status, stdout = commands.getstatusoutput(arg)

    # docker log
    print("-- ", stdout)
    log_split = stdout.split('\t')

    #print log_split
    if not log_split[0].find('AC') == -1:
      ac_count += 1
    else:
      wrong_result = log_split[0]
    if float(log_split[2]) > max_time:
      max_time = float(log_split[2])
  # retrieve exam info
  if not eid == None:
    sql = "SELECT `info` FROM `exam_question` WHERE `exam_id`='"+str(eid)+"' and `question_id`='"+str(qid)+"'"
    cursor.execute(sql)
    question = cursor.fetchall()
    decodejson =  json.loads(question[0][0])
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
  sql = "INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ("+str(summit_id)+",\""+str(end_result)+"\","+str(correctness)+",\""+str(judge_msg)+"\","+str(round(max_time, 3))+")"
  try:
    cursor.execute(sql)
    db.commit()
  except MySQLdb.Error as e:
    print('Error C {0}: {1}'.format(e.args[0], e.args[1]))

  # clean up
  status, stdout = commands.getstatusoutput("docker rm $(docker ps -a -q -f \"status=exited\")")
  status, stdout = commands.getstatusoutput("rm -rf share/"+str(summit_id))

def main():
  """ First, run retrieve() """
  start_time = timestamp()
  print(start_time, ' Daemon Starts. Your order is my command!')

  retrieve()

  """ initialize socket"""
  if not os.path.exists('/var/run/judge'):
    os.mkdir('/var/run/judge')
  serverAddr = '/var/run/judge/judge.sock'

  # Make sure the socket does not already exist
  try:
    os.unlink(serverAddr)
  except OSError:
    if os.path.exists(serverAddr):
      raise

  # Create socket
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

  # Bind the socket to the port
  sock.bind(serverAddr)

  # Grant www-data access
  status, stdout = commands.getstatusoutput("chown www-data:www-data /var/run/judge/judge.sock")

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
