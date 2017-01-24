from __future__ import absolute_import, with_statement, print_function
import subprocess
import threading
import time
import os
import signal

class Command(object):
  def __init__(self, cmd, args=None):
    self.cmd = './{0}'.format(cmd)
    self._args = args or []
    self.process = None
    self._tle = False
    self._time = 0
    self._run = False
    self._pipe = [None]

  def is_tle(self):
    return self._tle

  @property
  def runtime(self):
    return self._time

  @property
  def returncode(self):
    return self.process.returncode

  @property
  def out(self):
    return self._pipe[0]

  def run(self, fin, timeout):
    def target():
      start = time.time()
      args = self.cmd + self._args

      if fin:
        self.process = subprocess.Popen(
          args,
          stdin=fin,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT
        )
      else:
        self.process = subprocess.Popen(
          args,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT
        )
      self._pipe = self.process.communicate()
      self._run = True
      self._time = round(time.time() - start, 3)
    thread = threading.Thread(target=target)
    thread.start()

    thread.join(timeout)
    if thread.is_alive():
      self._tle = True
      os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
      thread.join()

# TODO: Migrate timeout implement
# http://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout
