
import threading
import socket
from lib import message
from lib import response

class ResponseHandler(threading.Thread):

	def __init__(self, client):
		threading.Thread.__init__(self)
		self.client = client

	def run(self):
		while True:
			try:
				msg = message.read(self.client.socket)
				if not msg:
					break
				resp = response.parse_type(msg)
				self.handle_response(resp)
			except Exception as e:
				self.client.print_error(e.message)

		self.client.socket.close()
		self.client.print_error("Server disconnected")

	def handle_response(self, resp):
		self.client.print_response(resp)


