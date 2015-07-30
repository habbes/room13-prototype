
import re
NAME_RE = re.compile(r'^[a-zA-Z\-_]+$')

class User:
	def __init__(self, address = "", name = ""):
		self.address = address
		self.name = name
		self.connection = None

	def set_address(self, addr, port):
		self.address = "%s:%s" % (addr, port)

	def send(self, msg):
		self.connection.send(msg.encode())

	def __str__(self):
		return "%s => %s" % (self.name, self.address) if self.name else self.address
