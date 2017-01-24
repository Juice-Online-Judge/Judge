from __future__ import absolute_import, with_statement, print_function
import os
from os import path
from stat import S_IRUSR, S_IRGRP, S_IROTH
import shutil

import docker

def build_container(base_path):
  client = docker.from_env()
  # Build judge image if not exist
  if not len(client.images.list(name='judge')):
    client.images.build(path=base_path)

def container(summit_id, code, test, ans, timelimit, memlimit):
  client = docker.from_env()
  shared_path = path.abspath(path.join('.', 'share', summit_id))
  code_path = path.join(shared_path, 'code.c')

  incount, outcount = prepare_container(shared_path, code, code_path, test, ans)

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

def prepare_container(shared_path, code, code_path, test, ans):
  incount = 0
  outcount = 0
  # make shared directory
  os.mkdir(shared_path)
  os.chmod(shared_path, S_IRUSR | S_IRGRP | S_IROTH)
  # copy student code
  shutil.copy(code, code_path)
  # copy test file
  for infile in test['files']:
    shutil.copy(
      path.join(test['basePath'], infile),
      path.join(shared_path, 'input_{0}'.format(incount))
    )
    incount += 1
  # copy ans file
  for outfile in ans['files']:
    shutil.copy(
      path.join(ans['basePath'], outfile),
      path.join(shared_path, 'output_{0}'.format(outcount))
    )
    outcount += 1
  if incount != outcount:
    print('incount != outcount')
    raise RuntimeError('incount != outcount')
  return (incount, outcount)
