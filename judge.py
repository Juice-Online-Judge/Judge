from __future__ import absolute_import, with_statement, print_function
"""
To-Do

- file open limit: ulimit -n

- memory limit: docker

- forbidden fuction: ?
"""

""" import """
import os
import sys
import subprocess
from subprocess import CalledProcessError
import threading
import locale
import time
import signal

""" define, function, class """

def usage():
  print('usage:')
  print('\tsummitID <stu code> <stdin> <sample ans> <time limit> <qid>')


""" command line arg. """
if len(sys.argv) != 7:
  usage()
  sys.exit()

summit_id = sys.argv[1]
stu_code = sys.argv[2]
stdin = sys.argv[3]
sample_ans = sys.argv[4]
time_limit = locale.atof(sys.argv[5])
qid = locale.atof(sys.argv[6])

# FIXME: Special case
special_case = [23, 26, 40, 41, 42, 43, 52, 54, 56]

try:
  fin = open(stdin, 'r')
  # FIXME: Special case
  # 40, 41: 2016PD_I_HW9
  # 42, 43: 2016PD_I_HW10
  # 54: PD final Q4
  # 56: PD final Q6
  # 52: PD final Q8
  if qid in special_case:
    ans_stdin = fin.read()
except IOError:
  # report("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mSample Input Not Found\033[00m")
  report('SE', 'Sample Input Not Found', '0', '0', '0')

try:
  fcode = open(stu_code, 'r')
except IOError:
  report('SE', 'Student Code Not Found', '0', '0', '0')

fcode = open(sample_ans, 'r')
ans_stdout = fcode.read()
ans_status = 0
if ans_status != 0:
  report('SE', 'Sample Answer Not Found', '0', '0', '0')

def compile(submit_id, std_code):
  args = ['gcc' '-std=gnu99' '-Werror' '-Wall' '-Wextra' '-o', submit_id, std_code]
  try:
    if qid != 37: # FIXME: Ban math.h
      args.append('-lm')
    subprocess.check_output(args, stderr=subprocess.STDOUT)
  except CalledProcessError as err:
    if not os.path.exists(summit_id):
      report('NE', 'No Executable File', 0, 0, 0)
    else:
      report('CE', err.output, '0', '0', '0')


""" main """
# compile
compile(submit_id, std_code)

# execute
# QA
if qid == 23:
  command = Command(summit_id, [stdin])

# 40, 41: 2016PD_I_HW9
# 42, 43: 2016PD_I_HW10
# 52: PD final Q8
# 54: PD final Q4
# 56: PD final Q6
elif qid in special_case:
  arg = ans_stdin.split('\n')
  command = Command(summit_id, [arg[0]])
else:
  command = Command(summit_id)

command.run(timeout=time_limit)
if command.process.returncode == -15 or command.tle():
  report('TLE','Time Limit Exceeded', command.runtime(), '0', '0')

""" delete tmp file """
clean()
