
import sys
import socket
from collections import namedtuple
from lib import request
from responsehandler import ResponseHandler
import os
import threading

EXIT = 'exit'
SEND = 'send'
BROADCAST = 'broadcast'
LIST = 'list'
NAME = 'name'
HELP = 'help'

PROMPT = ""
PROMPT2 = "> "
PROMPT3 = "<< "
BLOCKSTOP = ""

DEFAULT_PORT = 13500
DEFAULT_TIMEOUT = 10

Command = namedtuple('Command', ['name', 'params'])

class Client:

	def __init__(self, server_addr, port, **kw):
		self.prompt = kw.get('prompt', PROMPT)
		self.prompt2 = kw.get('prompt2', PROMPT2)
		self.prompt3 = kw.get('prompt3', PROMPT3)
		self.blockstop = kw.get('blockstop', BLOCKSTOP)
		self.users = {}
		self.usernames = {}
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_addr = (server_addr, port)

		#used to synchronize access to standard out
		self.print_lock = threading.Lock()


	def start(self):
		self.print_out(self.prompt3, "Connecting...")
		try:
			self.socket.connect(self.server_addr)
			self.print_out(self.prompt3, "Connection successful, accepting commands...")
		except:
			self.print_out(self.prompt3, "Connection failed, exiting...")
			return

		resphandler = ResponseHandler(self)
		resphandler.start()

		while True:
			cmd = self.get_command()
			if not cmd: continue
			self.handle_command(cmd)

	def print_out(self, *args, **kw):
		out =  " ".join(args)
		endl = kw.get('endl', True)
		if endl: out += "\n"
		self.print_lock.acquire()
		print out,
		self.print_lock.release()

	def get_command(self):
		c = raw_input(self.prompt)
		if not c: return
		parts = c.split()
		cmd = Command(parts[0].lower(), [p.strip() for p in parts[1:]])
		return cmd

	def get_block(self):
		lines = []
		self.print_lock.acquire()
		l = raw_input(self.prompt2)
		while not l == self.blockstop:
			lines.append(l)
			l = raw_input(self.prompt2)
		self.print_lock.release()
		return "\n".join(lines)

	def print_error(self, *e):
		out =  self.prompt3 + "-- ERROR:"
		for s in e: out += " " + s
		self.print_out(out)

	def print_head(self, cmd, *params):
		out = self.prompt3 + "-- SERVER: " + cmd
		for p in params: out += " " + p
		self.print_out(out)

	def print_response(self, resp):
		out = "\n" + self.prompt3 + "-- SERVER: " + resp.command
		for p in resp.params: out += " " + p
		if resp.content:
			out += "\n" + resp.content + "\n"
		#out += "\n" + self.prompt
		self.print_out(out)


	def print_block(self, s):
		self.print_out(s)

	def send(self, req, params, content = ""):
		try:
			self.socket.sendall(req(content, *params).encode())
		except:
			self.print_error("Error sending message to server")

	def send_block(self, req, params):
		content = self.get_block()
		self.send(req, params, content)

	def handle_command(self, cmd):
		handler = self.cmd_map.get(cmd.name)
		if not handler:
			self.print_error("Unknown command")
			return
		func, min_args = handler
		if len(cmd.params) < min_args:
			self.print_error("This command requires at least %d %s" % (min_args,
				"args" if min_args > 1 else "arg"))
			return
		func(self, cmd)

	def handle_send(self, cmd):
		self.send_block(request.SendRequest, cmd.params)

	def handle_broadcast(self, cmd):
		self.send_block(request.BroadcastRequest, cmd.params)

	def handle_list(self, cmd):
		self.send(request.ListRequest, cmd.params)

	def handle_name(self, cmd):
		self.send(request.NameRequest, cmd.params)

	def handle_help(self, cmd):
		out = self.prompt3 + "Available commands:"
		out += "\n%ssend <recipient> -> send message to specified name or address" % self.prompt3
		out += "\n%sslist -> request list of al current users" % self.prompt3
		out += "\n%sbroadcast -> send message to all users" % self.prompt3
		out += "\n%sname <name> -> request server to allocate you specified name" % self.prompt3
		out += "\n%sexit -> disconnect and exit" % self.prompt3
		out += "\n%shelp -> list available commands" % self.prompt3
		out += "\n%s" % self.prompt3
		out += "\n%sthe %s prompt indicates block or multiline input" % (self.prompt3, self.prompt2)
		if self.blockstop:
			out += "\n%s enter %s in it's own line to break input" % (self.prompt3, self.blockstop)
		else:
			out += "\n%sleave the last line empty to break input" % self.prompt3
		self.print_out(out)

	def handle_exit(self, cmd):
		self.close()

	def close(self, code = 0):
		self.socket.close()
		os._exit(code)

	cmd_map = {SEND: (handle_send, 1), BROADCAST: (handle_broadcast, 0),
				LIST: (handle_list, 0), NAME: (handle_name, 1),
				HELP: (handle_help, 0), EXIT: (handle_exit, 0)}


if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "Please specify server"
		sys.exit(1)
	addr = sys.argv[1]
	port = DEFAULT_PORT
	if len(sys.argv) > 2:
		port = sys.argv[2]
		try:
			port = int(port)
		except:
			print "Invalid port number"
			sys.exit(1)

	try:
		client = Client(addr, port)
		client.start()
	except socket.error as e:
		print "Failed to connect to server at %s:%s" % (addr, port)
	except Exception as e:
		print "Error:", e.message
		client.close()

