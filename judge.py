print 'hi'
"""
To-Do

- file open limit: ulimit -n

- memory limit: docker

- forbidden fuction: ?
"""

""" import """
import os
import sys
import commands
#from subprocess import call
import subprocess
import threading
import locale
import time

""" define, function, class """
def usage():
	print("usage:\n\tsummitID stuCode stdin sampleAns timeLimit")

def clean():
	subprocess.call(["rm", "-f", summitID])

#def judge(errtype, comment):
def judge(result, judge_msg, time, memory, openfile):
	memory = 0
	openfile = 0

	print result+'\t'+judge_msg+'\t'+str(time)+'\t'+str(memory)+'\t'+str(openfile)

	clean()
	sys.exit()

class Command(object):
		def __init__(self, cmd):
				self.cmd = cmd
				self.process = None

		def run(self, timeout):
				print "timeout = "+str(timeout)
				def target():
					start = time.time()
					self.process = subprocess.Popen(self.cmd, shell=True, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					pipe = self.process.communicate()
					runtime = round(time.time() - start, 3)
					#print("\033[01;36m%s seconds\033[00m" % runtime)

					if self.process.returncode == 139:
						#judge("\033[01;31mRuntime Error (RE)\033[00m", pipe[0])
						judge('RE', pipe[0], '0', '0', '0')
					elif self.process.returncode == 0:
						if pipe[0] == ans_stdout:
							#judge("\033[01;32mAccept (AC)\033[00m", None)
							judge('AC', 'N/A', runtime, '0', '0')
						else:
							#judge("\033[01;31mWrong Answer (WA)\033[00m", None)
							judge('WA', 'N/A', runtime, '0', '0')
				thread = threading.Thread(target=target)
				thread.start()

				print ">>>>>>>"+timeout
				thread.join(timeout)
				if thread.is_alive():
						self.process.terminate()
						thread.join()

""" command line arg. """
if len(sys.argv) != 6:
	usage()
	sys.exit()

summitID = sys.argv[1]
stuCode = sys.argv[2]
stdin = sys.argv[3]
sampleAns = sys.argv[4]
timeLimit = locale.atof(sys.argv[5])

try:
	fin = open(stdin, 'r')
except IOError:
	#judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mSample Input Not Found\033[00m")
	judge('SE', 'Sample Input Not Found', '0', '0', '0')
try:
	fcode = open(stuCode, 'r')
except IOError:
	#judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mStudent Code Not Found\033[00m")
	judge('SE', 'Student Code Not Found', '0', '0', '0')

ans_status, ans_stdout = commands.getstatusoutput("cat "+sampleAns)
if ans_status != 0:
	#judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mSample Answer Not Found\033[00m")
	judge('SE', 'Sample Answer Not Found', '0', '0', '0')

""" main """
runtime = 0
# compile
status, stdout = commands.getstatusoutput("gcc -o "+summitID+" "+stuCode)
if status>>8 == 1:
	#judge("\033[01;31mCompilor Error (CE)\033[00m", "\033[01;31m"+stdout+"\033[00m")
	judge('CE', stdout, '0', '0', '0')

# execute
command = Command("./"+summitID)
command.run(timeout=timeLimit)
if command.process.returncode == -15:
	#judge("\033[01;31mTime Limit Exceed (TLE)\033[00m", None)
	judge('TLE','N/A', runtime, '0', '0')
if command.process.returncode != 0 and command.process.returncode != 139:
	#judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mReason Unknown, Contact Admin!\033[00m")
	judge('SE', 'Judge Crashed in Container', '0', '0', '0')

""" delete tmp file """
clean()
