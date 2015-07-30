
import command
import message
from message import Message
import user
from user import User

class Request(Message):
	pass

class SendRequest(Request):
	"""Request used to send a message to a specific user"""
	def __init__(self, content, *params):
		Request.__init__(self, command.SEND, content, *params)
		if len(params) < 1: raise message.ParamError("Sender Address or Name is a required parameter")
		addr = self.params[0]
		if not user.NAME_RE.match(addr):
			self.recipient = User(addr)
		else: self.recipient = User("", addr)
		
		self.message = content

class BroadcastRequest(Request):
	"""Request used to send a message to all users"""
	def __init__(self, content, *params):
		Request.__init__(self, command.BROADCAST, content, *params)
		self.message = content

class ListRequest(Request):
	"""Request used to get a list of all logged in users"""
	def __init__(self, content, *params):
		Request.__init__(self, command.LIST, content, *params)

class NameRequest(Request):
	"""Request to register name"""
	def __init__(self, content, *params):
		Request.__init__(self, command.NAME, content, *params)
		if len(params) < 1: raise message.ParamError("Name is a required parameter")
		self.name = params[0]





TYPES = {command.SEND : SendRequest, command.LIST : ListRequest,
		command.BROADCAST : BroadcastRequest, command.NAME: NameRequest}

def parse_type(s):
	"""Parses the string to the correct request type"""
	return message.parse_type(s, TYPES)







