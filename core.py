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
	print("usage:\n\tsummitID stuCode stdin sampleAnsi timeLimit")

def clean():
	subprocess.call(["rm", "-f", summitID])

def judge(errtype, comment):
	print("/* Judge Respond */")
	print(errtype)
	if comment != None:
		print("/* Judge Comment */")
		print(comment)
	clean()
	sys.exit()

class Command(object):
		def __init__(self, cmd):
				self.cmd = cmd
				self.process = None

		def run(self, timeout):
				def target():
					start = time.time()
					self.process = subprocess.Popen(self.cmd, shell=True, stdin=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					pipe = self.process.communicate()
					print("/* Execute Time */")
					print("\033[01;36m%s seconds\033[00m" % (time.time() - start))

					#if self.process == 139:
					if pipe[0] == "Segmentation fault\n":
						judge("\033[01;31mRuntime Error (RE)\033[00m", pipe[0])
					elif self.process.returncode == 0:
						if pipe[0] == ans_stdout:
							judge("\033[01;32mAccept (AC)\033[00m", None)
						else:
							judge("\033[01;31mWrong Answer (WA)\033[00m", None)
				thread = threading.Thread(target=target)
				thread.start()

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
	judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mSample Input Not Found\033[00m")
try:
	fcode = open(stuCode, 'r')
except IOError:
	judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mStudent Code Not Found\033[00m")
ans_status, ans_stdout = commands.getstatusoutput("cat "+sampleAns)
if ans_status != 0:
	judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mSample Answer Not Found\033[00m")

""" main """
# compile
status, stdout = commands.getstatusoutput("gcc -o "+summitID+" "+stuCode)
if status>>8 == 1:
	judge("\033[01;31mCompilor Error (CE)\033[00m", "\033[01;31m"+stdout+"\033[00m")

# execute
command = Command("./"+summitID+"; sleep 3;")
command.run(timeout=timeLimit)
if command.process.returncode == -15:
	judge("\033[01;31mTime Limit Exceed (TLE)\033[00m", None)
if command.process.returncode != 0:
	judge("\033[01;31mSystem Error (SE)\033[00m", "\033[01;31mReason Unknown, Contact Admin!\033[00m")

""" delete tmp file """
clean()
