from __future__ import absolute_import, with_statement, print_function
import os
import sys
import subprocess
from subprocess import CalledProcessError
import locale

from command import Command, report, clean

def usage():
  print('usage:')
  print('\tsummitID <stu code> <STDIN> <sample ans> <time limit> <qid>')

if len(sys.argv) != 7:
  usage()
  sys.exit()

SUMMENT_ID = sys.argv[1]
STU_CODE = sys.argv[2]
STDIN = sys.argv[3]
SAMPLE_ANS = sys.argv[4]
TIME_LIMIT = locale.atof(sys.argv[5])
QID = locale.atof(sys.argv[6])

# FIXME: Special case
SPECIAL_CASE = [23, 26, 40, 41, 42, 43, 52, 54, 56]

try:
  FIN = open(STDIN, 'r')
  # FIXME: Special case
  # 40, 41: 2016PD_I_HW9
  # 42, 43: 2016PD_I_HW10
  # 54: PD final Q4
  # 56: PD final Q6
  # 52: PD final Q8
  if QID in SPECIAL_CASE:
    ANS_STDIN = FIN.read()
except IOError:
  # report("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mSample Input Not Found\033[00m")
  report('SE', 'Sample Input Not Found', '0', '0', '0')

try:
  FCODE = open(STU_CODE, 'r')
except IOError:
  report('SE', 'Student Code Not Found', '0', '0', '0')

FCODE = open(SAMPLE_ANS, 'r')
ANS_STDOUT = FCODE.read()

def compile_code(submit_id, std_code):
  args = ['gcc' '-std=gnu99' '-Werror' '-Wall' '-Wextra' '-o', submit_id, std_code]
  try:
    if QID != 37: # FIXME: Ban math.h
      args.append('-lm')
    subprocess.check_output(args, stderr=subprocess.STDOUT)
  except CalledProcessError as err:
    if not os.path.exists(SUMMENT_ID):
      report('NE', 'No Executable File', 0, 0, 0)
    else:
      report('CE', err.output, '0', '0', '0')

# compile
compile_code(SUMMENT_ID, STU_CODE)

# execute
# QA
if QID == 23:
  command = Command(SUMMENT_ID, [STDIN])

# 40, 41: 2016PD_I_HW9
# 42, 43: 2016PD_I_HW10
# 52: PD final Q8
# 54: PD final Q4
# 56: PD final Q6
elif QID in SPECIAL_CASE:
  arg = ANS_STDIN.split('\n')
  command = Command(SUMMENT_ID, [arg[0]])
  command.run(fin=None, timeout=TIME_LIMIT)
else:
  command = Command(SUMMENT_ID)
  command.run(fin=FIN, timeout=TIME_LIMIT)


if command.returncode == 134:
  report('RE', 'stack smashing detected', command.runtime, '0', '0')
elif command.returncode == -15:
  report('TLE.', 'Code Terminated (-15) Due to TLE', command.runtime, '0', '0')
elif not (0 < command.returncode < 127) and command.returncode != 255:
  report('RE', 'Segmentation fault ({0})'.format(command.returncode), command.runtime, '0', '0')
# QA
# FIXME: Seem useless
elif QID == 23:
  tmp_in = open(STDIN, 'r')
  tmp_out = open(SAMPLE_ANS, 'r')
  if tmp_in.read() == tmp_out.read():
    report('AC', 'Accepted', command.runtime, '0', '0')
    report('WA', 'Wrong Answer', command.runtime, '0', '0')
    report('WA', 'Wrong Answer', command.runtime, '0', '0')
# End QA
    report('AC', 'Accepted', command.runtime, '0', '0')
    report('WA', 'No Output', command.runtime, '0', '0')
  else:
    report('WA', 'Wrong Answer', command.runtime, '0', '0')
else:
  report('WA', 'Wrong Answer', command.runtime, '0', '0')

if command.returncode == -15 or command.is_tle():
  report('TLE', 'Time Limit Exceeded', command.runtime, '0', '0')

clean(SUMMENT_ID)
