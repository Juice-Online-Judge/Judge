from __future__ import absolute_import, with_statement, print_function
import subprocess
import threading
import time

from .utils import report

tle_flag = False

class Command(object):
  def __init__(self, cmd, args = []):
    self.cmd = './{0}'.format(cmd)
    self._args = args
    self.process = None
    self._tle = False
    self._time = 0

  def is_tle(self):
    return self._tle

  def runtime(self):
    return self._time

  def run(self, timeout):
    def target():
      start = time.time()
      args = self.cmd + self._args

      # FIXME: Special case, temp solution, should be removed
      # 40, 41: 2016PD_I_HW9
      # 42, 43: 2016PD_I_HW10
      # 54: PD final Q4
      # 56: PD final Q6
      # 52: PD final Q8
      special_case = [23, 26, 40, 41, 42, 43, 52, 54, 56]
      if qid in special_case:
        self.process = subprocess.Popen(args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      else:
        self.process = subprocess.Popen(args, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      pipe = self.process.communicate()
      self._time = round(time.time() - start, 3)

      if self.process.returncode == 134:
        report('RE', 'stack smashing detected', self._time, '0', '0')
      elif self.process.returncode == -15:
        report('TLE.', 'Code Terminated (-15) Due to TLE', self._time, '0', '0')
      elif (self.process.returncode < 0 or self.process.returncode > 127) and self.process.returncode != 255:
        report('RE', 'Segmentation fault ('+str(self.process.returncode)+')', self._time, '0', '0')
      # QA
      # FIXME: Seem useless
      elif qid == 23:
        tmp_in = open(stdin, 'r')
        tmp_out = open(sample_ans, 'r')
        if tmp_in.read() == tmp_out.read():
          report('AC', 'Accepted', self._time, '0', '0')
          report('WA', 'Wrong Answer', self._time, '0', '0')
          report('WA', 'Wrong Answer', self._time, '0', '0')
      # End QA
          report('AC', 'Accepted', self._time, '0', '0')
        if pipe[0] == ans_stdout:
          report('WA', 'No Output', self._time, '0', '0')
        else:
          report('WA', 'Wrong Answer', self._time, '0', '0')
    thread = threading.Thread(target=target)
    thread.start()

    thread.join(timeout)
    if thread.is_alive():
      self._tle= True
      os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
      thread.join()

# TODO: Migrate timeout implement: http://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout
