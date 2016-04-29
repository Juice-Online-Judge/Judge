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
#def signal_handler(signal, frame):
#	die_time = time.strftime("%Y-%m-%d %H:%M:%S")
#	print die_time+' Good Bye. It has been an honour!'
#	sys.exit(0)

def timestamp():
	print time.strftime("%Y-%m-%d %H:%M:%S")

def retrieve():
	global cursor
	sql = "SELECT `id`, `question_id`, `exam_id`, `code` FROM `submissions` WHERE `id` NOT IN (SELECT `submission_id` FROM `judges`)"
	try:
		# execute SQL statement
		cursor.execute(sql)
	except MySQLdb.Error as e:
		print "Error B %d: %s" % (e.args[0], e.args[1])

	summit = cursor.fetchall()
	# retrieve all results
	if not summit:
		rest_time = time.strftime("%Y-%m-%d %H:%M:%S")
		print rest_time+' Judge rests. All done!'
		return

	# retrieve result one by one
	for record in summit:
		sid = record[0]
		qid = record[1]
		eid = record[2]
		code = record[3]

		# restrict function
		header = '[a-z|A-Z|\/|0-9]*[\.]h'
		CODE = open(code, 'r')
		pat = re.findall(header, CODE.read())
		for  pp in pat:
			if not pp in whitefunc:
				# insert to TABLE judge
				end_time = time.strftime("%Y-%m-%d %H:%M:%S")
				print end_time+' Judge Finished: submission_id='+str(sid)+', result=RF, correctness=0'
				sql = "INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ("+str(sid)+",\"RF\",0,\"N/A\",0)"
				try:
					cursor.execute(sql)
					db.commit()
				except MySQLdb.Error as e:
					print "Error A %d: %s" % (e.args[0], e.args[1])
				return

		#function = '[a-z|A-Z|0-9|\_][\(]*[\)]'
		for black in blackfunc:
			if not CODE.read().find(black) == -1:
				print CODE.read()
				end_time = time.strftime("%Y-%m-%d %H:%M:%S")
				print end_time+' Judge Finished: submission_id='+str(sid)+', result=RF, correctness=0'
				sql = "INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ("+str(sid)+",\"RF\",0,\"N/A\",0)"
				try:
					cursor.execute(sql)
					db.commit()
				except MySQLdb.Error as e:
					print "Error A %d: %s" % (e.args[0], e.args[1])
				return

		# retrieve question info
		sql = "SELECT `id`, `judge` FROM `questions` WHERE `id`='"+str(qid)+"'"
		cursor.execute(sql)
		question = cursor.fetchall()
		decodejson =  json.loads(question[0][1])

		# initial judge in docker
		ini_time = time.strftime("%Y-%m-%d %H:%M:%S")
		print ini_time+' Judge Initiate: sumission_id='+str(sid)
		docker(sid, code, decodejson['input'], decodejson['output'], decodejson['restriction']['time'], decodejson['restriction']['memory'], qid, eid)

	# close connection
	#db.close()

def docker(summitID, code, test, ans, timelimit, memlimit, qid, eid):
	incount = 0;
	outcount = 0;
	# make shared directory
	status, stdout = commands.getstatusoutput("mkdir share/"+str(summitID))
	status, stdout = commands.getstatusoutput("chmod 444 share/"+str(summitID))
	# copy judge.py
	status, stdout = commands.getstatusoutput("cp judge.py share/"+str(summitID)+"/.")
	# copy student code
	status, stdout = commands.getstatusoutput("cp "+code+" share/"+str(summitID)+"/code.c")
	# copy test file
	for infile in test['files']:
		status, stdout = commands.getstatusoutput("cp "+test['basePath']+"/"+infile+" share/"+str(summitID)+"/input_"+str(incount))
		incount += 1
	# copy ans file
	for outfile in ans['files']:
		status, stdout = commands.getstatusoutput("cp "+ans['basePath']+"/"+outfile+" share/"+str(summitID)+"/output_"+str(outcount))
		outcount += 1

	if incount != outcount:
		print("error: file count mismatch, stopping!")

	# docker
	ac_count = 0
	max_time = 0.0
	wrong_result = ''
	while incount > 0:
		incount -= 1
		if int(memlimit) < 3:
			memlimit = 3
		print "- running with testfile: "+str(incount)
		arg = "docker run -m "+str(int(memlimit)+1)+"m -v /home/silenttulips/share/"+str(summitID)+":/share ubuntu:latest /usr/bin/python2.7 /share/judge.py "+str(summitID)+" /share/code.c /share/input_"+str(incount)+" /share/output_"+str(incount)+" "+str(timelimit)
		status, stdout = commands.getstatusoutput(arg)

		# docker log
		print "-- "+stdout
		log_split = stdout.split('\t')

		#print log_split
		if not log_split[0].find('AC') == -1:
			#global ac_count
			ac_count += 1
		else:
			#xxx = log_split[0].split('\n')
			#wrong_result = xxx[-1]
			wrong_result = log_split[0]
			#wrong_result = re.findall('(?WA)|(?TLE)|(?MLE)|(?CE)|(?RE)|(?SE)', log_split[0])
		if float(log_split[2]) > max_time:
			max_time = float(log_split[2])
	# retrieve exam info
	if not eid == None:
		sql = "SELECT `info` FROM `exam_question` WHERE `exam_id`='"+str(eid)+"' and `question_id`='"+str(qid)+"'"
		#sql = "SELECT `info` FROM `exam_question` WHERE `exam_id`=27 AND `question_id`=46"
		cursor.execute(sql)
		question = cursor.fetchall()
		decodejson =  json.loads(question[0][0])
		qtype = decodejson['type']
	else:
		qtype = None
	#print decodejson
	# final scoring
	#end_result = ''
	#judge_msg = ''
	#correctness = ''
	#print decodejson['type']
	#print ac_count
	#print outcount
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
		#end_result = "PC"
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
	end_time = time.strftime("%Y-%m-%d %H:%M:%S")
	#print end_result
	print end_time+' Judge Finished: submission_id='+str(summitID)+', result='+end_result+', correctness='+correctness
	sql = "INSERT INTO `judges` (`submission_id`, `result`, `correctness`, `judge_message`, `time`) VALUES ("+str(summitID)+",\""+str(end_result)+"\","+str(correctness)+",\""+str(judge_msg)+"\","+str(round(max_time, 3))+")"
	try:
		cursor.execute(sql)
		db.commit()
	except MySQLdb.Error as e:
		print "Error C %d: %s" % (e.args[0], e.args[1])

	# clean up
	status, stdout = commands.getstatusoutput("docker rm $(docker ps -a -q -f \"status=exited\")")
	status, stdout = commands.getstatusoutput("rm -rf share/"+str(summitID))

""" +------------------------------+ """
""" |   Main Fucntion Start Here   | """
""" +------------------------------+ """

""" First, run retrieve() """

start_time = time.strftime("%Y-%m-%d %H:%M:%S")
print start_time+' Daemon Starts. Your order is my command!'

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
#status, stdout = commands.getstatusoutput("chmod g+w /var/run/judge/judge.sock")

# Listen for incoming connections
sock.listen(1)

""" daemon """
while True:

	#signal.signal(signal.SIGINT, signal_handler)
	#signal.pause()

	# Wait for a connection
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
