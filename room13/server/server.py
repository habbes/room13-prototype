import socket
import threading
import sys
from clienthandler import ClientHandler

DEFAULT_PORT = 13500
DEFAULT_HOST = ''


class Server:
	def __init__(self, addr, port):
		self.address = addr
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((addr, port))
		self.socket.listen(5)
		self.users = {}
		self.usernames = {}
		#used to synchronize access to users dict
		self.users_lock = threading.Lock()
		self.handlers = []
		self.should_exit = False
		self.socket.settimeout(5)

	def start(self):
		print  'Server is ready and listening at port %s' % self.port 
		while not self.should_exit:
			try:
				conn, addr = self.socket.accept()
			except socket.timeout:
				#rerun the loop after timeout to make handle exit requests
				continue
			print 'Client connection - ', "%s:%s" % addr
			handler = ClientHandler(self, conn, addr)
			self.handlers.append(handler)
			handler.start()

	def add_user(self, user):
		with self.users_lock:
			self.users[user.address] = user

	def remove_user(self, user):
		with self.users_lock:
			self.users.pop(user.address, None)
			if user.name: self.usernames.pop(user.name, None)

	def register_name(self, name, user):
		self.users_lock.acquire()
		if name in self.usernames:
			self.users_lock.release()
			return None
		self.usernames[name] = user
		#free previously registered name, if any
		if user.name: self.usernames.pop(user.name, None)
		self.users_lock.release()
		user.name = name
		return True

	def get_user(self, user):
		self.users_lock.acquire()
		if user.address:
			u = self.users.get(user.address)
		elif user.name:
			u = self.usernames.get(user.name)
		self.users_lock.release()
		return u

	def for_each_user(self, func, skip = []):
		with self.users_lock:
			for addr in self.users:
				u = self.users[addr]
				if u not in skip:
					func(u)

	def get_users(self):
		self.users_lock.acquire()
		us = self.users.values()
		self.users_lock.release()
		return us

	def request_close(self):
		self.socket.close()
		self.should_exit = True
		for handler in self.handlers:
			if handler.is_alive():
				handler.request_close()
		



if __name__ == '__main__':
	args = sys.argv[1:]
	port = DEFAULT_PORT
	host = DEFAULT_HOST
	if len(sys.argv) > 1:
		port = sys.argv[1]

	try:
		port = int(port)
	except:
		print "Invalid port number"
		sys.exit(1)

	try:
		server = Server(host, port)
		server_thread = threading.Thread(target = server.start)
		server_thread.start()
	except Exception as e:
		print "Error connecting", e.message
		sys.exit(1)

	command = raw_input("Type 'exit' to close\n")
	while command != 'exit':
		command = raw_input()

	print "Requesting server to stop"
	server.request_close()
	for th in threading.enumerate():
		try:
			th.join()
		except:
			continue

	print "Exiting"
