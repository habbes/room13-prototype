
import re
import error

class MessageError(Exception):
	def __init__(self, *args):
		Exception.__init__(self, *args)
		self.type = str(self.errtype)

class FormatError(MessageError): errtype = error.FORMAT
class UnknownCommandError(MessageError): errtype = error.COMMAND_UNKNOWN
class ParamError(MessageError): errtype = error.PARAM
class IncompleteError(MessageError): errtype = error.INCOMPLETE

class Message:
	"""Represents a message from client or server"""
	def __init__(self, cmd, content, *params):
		self.command = cmd.strip().upper()
		self.params = params
		self.content = content

	def add_param(self, param):
		self.params.append(param)

	def encode(self):
		s = self.command.strip().upper()
		if self.params:
			s = "%s %s" % (s, " ".join(str(p).strip() for p in self.params))
		if self.content:
			s = "%s\n%s" % (s, self.content)
		s = s.encode()
		s = "%s\n%s" % (len(s), s)
		return s.encode()


	def __str__(self):
		return self.encode()

	@classmethod
	def from_dict(cls, d):
		return cls(d['command'], d['content'], *d['params'])

	@classmethod
	def parse(cls, s):
		return cls.from_dict(parse_to_dict(s))


def parse_to_dict(s):
	"""Parse request string -> Dict with 'command' and 'params' as keys"""
	parts = re.split(r'(?:\r\n)|[\r\n]', s, 1)
	head = parts[0]
	content = parts[1] if len(parts) > 1 else ""
	headparts = [part.strip() for part in head.split()]
	return {'command': headparts[0], 'params': headparts[1:], 'content':content}

def parse_type(s, types):
	"""Parses the string and returns the specific subclass that 
	matches the command from the types dict"""

	d = parse_to_dict(s)
	cmd = d['command']
	cls = types.get(cmd)
	if cls: return cls(d['content'], *d['params'])
	raise UnknownCommandError("Unknown command '%s'" % cmd)

def read(conn):
	"""reads an entire message from a socket connection and returns a string"""
	#the message is encoded as follow
	#<length>
	#<command> <param1> <param2> <...>
	#<content>

	#length specifies the length of the message from the start of <command>
	lbuffer = []
	c = conn.recv(1)
	if not c: return None

	while c != "\n":
		lbuffer.append(c)
		c = conn.recv(1)
		if not c: return None
		
	length = "".join(lbuffer)
	try:
		length = int(length)
	except:
		raise FormatError("Unable to determine Length")

	#get message
	received = 0
	bufsize = 2048
	chunks = []
	while received < length:
		chunk = conn.recv(min(length - received, bufsize))
		if not chunk:
			return None
		chunks.append(chunk)
		received += len(chunk)
	msg = ''.join(chunks)
	return msg.decode()

	