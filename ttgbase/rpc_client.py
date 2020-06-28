# -*- coding: utf-8 -*-

from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError

import json
from time import sleep, time
from pprint import pprint
from itertools import cycle

from .proxy import Proxy
import threading

nodes = ['https://api.telegram.org']
#nodes = ['https://api.telegram.org/bot']

class Http():

	http = Session()
	proxies = None


class RpcClient(Http):

	""" Simple Telegram JSON-RPC API
		rpc = RpcClient(token)
		any call available to that port can be issued using the instance
		rpc.call('command', *parameters)
	"""
	
	RPS_DELAY = 0.34	# ~3 requests per second
	last_request = 0.0
	
	headers = {'User-Agent': 'thallid', 'content-type': 'application/json'}
	
	def __init__(self, token, **kwargs):

		self.report = kwargs.get("report", False)
		self.PROXY = kwargs.get("PROXY", False)
		if self.PROXY: self.proxies = Proxy()
		self.token = token

		self.nodes = cycle(nodes)		# Перебор нод
		self.url = next(self.nodes)
		
		self.num_retries = kwargs.get("num_retries", 3)		# Количество попыток подключения к ноде
		#adapter = HTTPAdapter(max_retries=self.num_retries)
		#for node in nodes:
		#	self.http.mount(node, adapter)
			
		self.lock = threading.Lock()					#http://www.quizful.net/post/thread-synchronization-in-python
			
		
	def get_response(self, name, payload):
	
		#data = json.dumps(payload, ensure_ascii=False).encode('utf8')
		files = payload.pop("files", None)
	
		while True:
				
			n = 1
			proxies = self.proxies.get_http() if self.PROXY else None
			while n <= self.num_retries:
				try:
					url = '/'.join([self.url, 'bot' + self.token, name])
					#print(self.token, name, data, proxies, url)
					#print(url, proxies)
					
					#response = self.http.post(url, data=data, headers=self.headers, proxies=proxies)
					
					response = self.http.request('get', url, params=payload, files=files, proxies=proxies, timeout=5)
					
					return response
					
				except:
					#print('ce', ce)
					sleeptime = (n - 1) * 2 + 1	#54321
					if self.report:
						print("Lost connection to %s (%d/%d) " % (self.url, n, self.num_retries))
						print("Retrying in %d seconds" % sleeptime)
					sleep(sleeptime)
					n += 1
					
			#self.url = next(self.nodes)			# next node
			proxies = self.proxies.new_http() if self.PROXY else None	# next proxy
			print('new proxy', proxies)
			#if self.report: print("Trying to connect to node %s" % url, 'error in get_response', proxies)
				
		return False

					
	def call(self, name, *params, **kwargs):
	
		payload = {cmd: kwargs[cmd] for cmd in kwargs}
		
		n = 1
		while n <= self.num_retries:
			with self.lock:
				# Ограничение 3 запроса в секунду
				delay = self.RPS_DELAY - (time() - self.last_request)
				if delay > 0: sleep(delay)
				
				response = self.get_response(name, payload)
				self.last_request = time()
				
				if response:
					#if response.status_code != 200:
					if response.ok:
						try:
							tx = response.json()
							if 'error' in tx: pprint(tx["error"])
							return tx["result"]
						except:
							print('ERROR JSON', response)
					else:
						if self.report: print(n, 'ERROR status_code', response.status_code, response.text)
				else:
					print('not connection to node', self.url)
				
			#print('response', response)
			n += 1
			self.url = next(self.nodes)			# next node
			sleep(n * 2)
			print(n, self.num_retries, 'Trying', self.url, 'for method', name, self.proxies.get_http())
		
		print('ERROR CALL')
		return None


#----- main -----
if __name__ == '__main__':
	pass