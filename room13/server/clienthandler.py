
import threading
import socket
from lib import message
from lib import user
from lib import request
from lib import response
from lib import error
from lib import command
from lib import event


class ClientHandler(threading.Thread):

	def __init__(self, server, conn, address):
		threading.Thread.__init__(self)
		self.server = server
		self.connection = conn
		self.user = user.User()
		self.user.set_address(address[0], address[1])
		self.user.connection = conn
		self.should_exit = False
		self.connection.settimeout(1)

	def run(self):
		self.server.add_user(self.user)
		self.notify_others("%s joined the room" % (self.user), event.USER_JOINED, self.user.address)
		while not self.should_exit:
			try:
				msg = message.read(self.connection)
				if not msg:
					break
				req = request.parse_type(msg)

				self.handle_request(req)
			except (message.ParamError, message.IncompleteError, 
				message.UnknownCommandError, message.FormatError) as e:
				self.user.send(response.ErrorResponse(e.message, e.type))
				continue
			except socket.timeout:
				continue
				#go back up to check for exit requests
			except socket.error as e:
				print "Connection Error: ", e.message
				break
			except Exception as e:
				print "Error: ", e.message
			

		self.close_connection()
		self.server.remove_user(self.user)
		try:
			self.notify_others("%s has left the room" % str(self.user), event.USER_LEFT, self.user.address)
		except:pass
		print 'Client disconnected -', self.user.address

	def request_close(self):
		self.close_connection()
		self.should_exit = True

	def close_connection(self):
		try:
			self.connection.shutdown(socket.SHUT_RDWR)
		except: pass
		self.connection.close()

	def handle_request(self, req):
		handler = self.cmd_map[req.command]
		handler(self, req)

	def handle_send(self, req):
		u = self.server.get_user(req.recipient)
		if u:
			params = [self.user.address]
			if self.user.name: params.append(self.user.name)
			u.send(response.MessageResponse(req.message, *params))
			self.user.send(response.OKResponse())
		else:
			self.user.send(response.ErrorResponse("Recipient is unknown", error.USER_UNKNOWN))

	def handle_broadcast(self, req):
		params = [self.user.address]
		if self.user.name: params.append(self.user.name)
		self.send_to_others(response.MessageResponse(req.message, *params))
		self.user.send(response.OKResponse())

	def handle_list(self, req):
		us = self.server.get_users()
		content = "\n".join(("%s\t%s" % (u.address, u.name)) if u.name else ("%s" % u.address) for u in us)
		self.user.send(response.ListResponse(content))

	def handle_name(self, req):
		if self.server.register_name(req.name, self.user):
			self.user.send(response.OKResponse())
			self.notify_others("%s has registered name %s" % (str(self.user), req.name),
				 event.NAME_REGISTERED, self.user.address, req.name)
		else:
			self.user.send(response.ErrorResponse("Server refused to register the name", error.NAME_USED))

	@staticmethod
	def send_to_user(user, msg):
		#send to user and ignore error on failure
		try:
			user.send(msg)
		except:
			pass

	def send_to_others(self, msg):
		self.server.for_each_user(lambda u: self.send_to_user(u, msg), [self.user])

	def notify_others(self, msg, *params):
		self.send_to_others(response.EventResponse(msg, *params))

	#maps commands to request handlers
	cmd_map = {command.SEND: handle_send, command.LIST: handle_list,
			command.BROADCAST: handle_broadcast, command.NAME: handle_name}
			
			
			

