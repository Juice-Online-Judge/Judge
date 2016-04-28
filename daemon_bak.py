""" import """
import socket
import sys
import os
import commands
import MySQLdb
import json

""" define, function, class """
def retrieve():
	try:
		db = MySQLdb.connect("mysql.cs.ccu.edu.tw","cchuo102u","123456","cchuo102u_juice",charset='utf8')

		sql = "SELECT `id`, `question_id`, `exam_id`, `code` FROM `submissions` WHERE `id` NOT IN (SELECT `submission_id` FROM `judges`)"

		# execute SQL statement
		cursor = db.cursor()
		cursor.execute(sql)

		# retrieve all results
		summit = cursor.fetchall()
		if not summit:
			print "\n-----------------"
			print "Judge All done :)"
			print "-----------------\n"
			return

		# retrieve result one by one
		for record in summit:
			sid = record[0]
			qid = record[1]
			eid = record[2]
			code = record[3]
			#print "%d, %d, %s, %s" % (sid, qid, eid, code)
			print "-----------------"
			print code

			# retrieve question info
			sql = "SELECT `id`, `judge` FROM `questions` WHERE `id`='"+str(qid)+"'"
			cursor.execute(sql)
			question = cursor.fetchall()
			#print question[0][1]

			decodejson =  json.loads(question[0][1])

			docker(sid, code, decodejson['input'], decodejson['output'], decodejson['restriction']['time'])

		# close connection
		db.close()
	except MySQLdb.Error as e:
		print "Error %d: %s" % (e.args[0], e.args[1])

def docker( summitID, code, test, ans, time):
	print("\nJudge Iniitiate")
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
	while incount > 0:
		incount -= 1
		outcount -= 1
		print "------------"
		print "running with testfile: "+str(incount)
		print "------------"
		arg = "docker run -v /home/silenttulips/share/"+str(summitID)+":/share ubuntu:latest /usr/bin/python2.7 /share/judge.py "+str(summitID)+" /share/code.c /share/input_"+str(incount)+" /share/output_"+str(outcount)+" "+str(time)
		status, stdout = commands.getstatusoutput(arg)

		# docker log
		print(stdout)

	# clean up
	status, stdout = commands.getstatusoutput("docker rm $(docker ps -a -q)")
	status, stdout = commands.getstatusoutput("rm -rf share/"+str(summitID))

""" First, run retrieve() """
retrieve()

""" initialize socket"""
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
status, stdout = commands.getstatusoutput("chgrp www-data /var/run/judge/judge.sock")
status, stdout = commands.getstatusoutput("chmod g+w /var/run/judge/judge.sock")

# Listen for incoming connections
sock.listen(1)

""" daemon """
while True:
	# Wait for a connection
	connection, client_address = sock.accept()
	try:
		msg = connection.recv(16)
		if msg:
			# Perform SQL query
			retrieve()

	finally:
		# Clean up the connection
		connection.close()
