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
tle_flag = False

def usage():
	print("usage:\n\tsummitID stuCode stdin sampleAns timeLimit")

def clean():
	#subprocess.call(["rm", "-rf", summitID])
	if os.path.exists(summitID):
		os.unlink(summitID)

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
				def target():
					start = time.time()
					self.process = subprocess.Popen([self.cmd], shell=False, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
							judge('WA', 'Wrong Answer', runtime, '0', '0')
				thread = threading.Thread(target=target)
				thread.start()

				thread.join(timeout)
				if thread.is_alive():
						#print "tle_flag"
						global tle_flag
						tle_flag = True
						self.process.kill()
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
status, stdout = commands.getstatusoutput("gcc -o "+summitID+" "+stuCode+" -lm")
if status>>8 == 1:
	#judge("\033[01;31mCompilor Error (CE)\033[00m", "\033[01;31m"+stdout+"\033[00m")
	judge('CE', stdout, '0', '0', '0')
if not os.path.exists(summitID):
	judge('NE', 'No Executable File', 0, 0, 0)

# execute
command = Command("./"+summitID)
command.run(timeout=timeLimit)
if command.process.returncode == -15 or tle_flag == True:
	#judge("\033[01;31mTime Limit Exceed (TLE)\033[00m", None)
	judge('TLE','Time Limit Exceeded', runtime, '0', '0')
elif command.process.returncode != 0 and command.process.returncode != 139:
	#judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mReason Unknown, Contact Admin!\033[00m")
	#judge('SE', 'Judge Crashed in Container', '0', '0', '0')
	judge('MLE', 'Memory Limit Exceeded', '0', '0', '0')
""" delete tmp file """
clean()
