from __future__ import absolute_import, with_statement, print_function
import os
import sys

def clean(summit_id):
  if os.path.exists(summit_id):
    os.unlink(summit_id)

def report(result, judge_msg, time, memory, openfile):
  openfile = 0
  log = '\t'.join([result, judge_msg, time, memory, openfile])
  print(log)
  clean()
  sys.exit()
