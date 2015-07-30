
import command
import message
from message import Message
import re
from user import User
import user

class Response(Message):
	"""Represents a message from server to client"""
	def __init__(self, cmd, content="", *params):
		Message.__init__(self, cmd, content, *params)
		self.content = content

class OKResponse(Response):
	"""Response indicating success"""
	def __init__(self, content="", *params):
		Response.__init__(self, command.OK, content, *params)

class ListResponse(Response):
	"""Response that lists current users"""
	def __init__(self, content="", *params):
		Response.__init__(self, command.LIST, content, *params)
		self.users = []
		for entry in content.splitlines():
			parts = re.split(r'\s+',entry.strip(),1)
			u = User(parts[0])
			if len(parts) > 1:
				u.name = parts[1]
			self.users.append(u)

	


class ErrorResponse(Response):
	"""Response indicating an error"""
	def __init__(self, content, *params):
		Response.__init__(self, command.ERROR, content, *params)
		if len(params) < 1: raise message.ParamError("Error Type is a required parameter")
		self.type = int(params[0])
		self.message = content

#this is technically not a response since it does not result from any request
class EventResponse(Response):
	"""Message notifying of an occured event"""
	def __init__(self, content, *params):
		Response.__init__(self, command.EVENT, content, *params)
		if len(params) < 1: raise message.ParamError("Event Type is a required parameter")
		self.type = int(params[0])
		self.message = content

class MessageResponse(Response):
	"""Carries user's message to other users"""
	def __init__(self, content, *params):
		Response.__init__(self, command.MESSAGE, content, *params)
		if len(params) < 1: raise message.ParamError("Sender Address is a required parameter")
		addr = self.params[0]
		self.sender = User(addr)
		if len(params) > 1: self.sender.name = self.params[1]
		self.message = content


TYPES = {command.OK : OKResponse, command.LIST : ListResponse,
		command.ERROR : ErrorResponse, command.EVENT : EventResponse,
		command.MESSAGE : MessageResponse}


def parse_type(s):
	"""Parses the string to the correct response type"""
	return message.parse_type(s, TYPES)
