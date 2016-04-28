""" import """
import socket
import sys
import os
import commands

""" initialize socket"""
serverAddr = '/var/run/judge/judge.sock'

# Create a UDS socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    sock.connect(serverAddr)
except socket.error, msg:
    print >>sys.stderr, msg
    sys.exit(1)

if len(sys.argv) != 2:
	string = 'ping'
else:
	string = sys.argv[1]

""" judge iniitiate """
sock.sendall(string)

# Clean up the connection
sock.close()
