# -*- coding: utf-8 -*-

import requests
import threading
import json

from time import time, sleep
from pprint import pprint


class Api(object):

	RPS_DELAY = 0.34  # ~3 requests per second
	BOT_WAIT = 25
	last_request = 0.0

	url = 'https://api.telegram.org/bot'
	offset = 0
	
	def __init__(self, token):
	
		url = self.url + token + '/'
		
		self.cmd = {
					"getMe": url + 'getMe',
					"getUpdates": url + 'getUpdates',
					"sendMessage": url + 'sendMessage',
					}
	
		# private_text: function итд
		types = ['private', 'chat']
		events = ['text', 'reply', 'entities', 'forward', 'photo', 'document', 'sticker']
		cmds = ['_'.join([type, event]) for type in types for event in events]
		self.commands = {cmd: self.command_pass for cmd in cmds}
					
		self.http = requests.Session()
		self.lock = threading.Lock()					#http://www.quizful.net/post/thread-synchronization-in-python

		print('check BOT telegram')
		tx = self.get_me()
		if tx:
			bot_name = tx["username"]
			print(bot_name, 'ok')
		else:
			print('ERROR', token)
		
		
	##### ##### ##### ##### #####
	
	def run(self):
	
		# self.commands функции которые надо вызвать на новые сообщения
		self.flag = True
		bot_thread = threading.Thread(target = self.scan, daemon = True)
		bot_thread.start()

		
	def scan(self):
	
		# Необходимо загрузить функции commands
	
		while self.flag:

			updates = self.get_updates_limit()		# Считываем тока по одному сообщению
			for tx in updates:
				
				message = tx.get("message", None)
				edited = False if message else True
				# Потом подумать что делать с редактироанием сообщений и как реагировать боту
				#if not message:
				#	message = tx.get("edited_message", None)
				
				#resolve
				#chat_id = tx["message"]["chat"].get("id")
				#from_id = tx["message"]["from"].get("id")
				#from_language = tx["message"]["from"].get("language_code")
				#is_bot = tx["message"]["from"].get("is_bot")		# бот не может получить мессаги от ботов
				
				if message:

					text = tx["message"].get("text", None)
					photo = tx["message"].get("photo", None)		# [], photo_text = tx["message"].get("caption", '')
					document = tx["message"].get("document", None)
					sticker = tx["message"].get("sticker", None)

					private = True if tx["message"]["chat"]["type"] == 'private' else False		# aka private or supergroup
					
					reply = True if tx["message"].get("reply_to_message", None) else False
					forward = True if tx["message"].get("forward_from", None) else False
					entities = True if tx["message"].get("entities", None) else False
					
					if text and private and not reply and not entities:
						self.commands["private_text"](tx["message"])			# Сообщение боту
					elif text and not private and not reply and not entities:
						self.commands["chat_text"](tx["message"])				# Сообщение в группе
						
					elif text and private and reply and not entities:
						self.commands["private_reply"](tx["message"])
					elif text and not private and reply and not entities:
						self.commands["chat_reply"](tx["message"])
					
					elif text and private and not reply and entities:
						self.commands["private_entities"](tx["message"])		# Команда боту
					elif text and not private and not reply and entities:
						self.commands["chat_entities"](tx["message"])			# Команду в группе боту
					else:
						pprint(tx)
						
				else:
					pprint(tx)
				
				self.offset = tx["update_id"] + 1
				#input('next')
	
			sleep(self.RPS_DELAY)		### так же задействовать таймер сообщений, но необязательно так как при самом запросе есть лимит уже
			
			
	def command_pass(self, message):
		pass


	def get_me(self):
		return(self.method('getMe'))

		
	def get_updates(self):
		return(self.method('getUpdates'))
		
		
	def get_updates_limit(self):
		return(self.method('getUpdates', values = {"offset": self.offset, "limit": 1}))
		
	def send_message(self, chat_id, text, **kwargs):
		
		parse_mode = kwargs.get("parse_mode", None)
		disable_web_page_preview = kwargs.get("disable_web_page_preview", None)
		disable_notification = kwargs.get("disable_notification", None)
		reply_to_message_id = kwargs.get("reply_to_message_id", None)
		
		reply_markup = kwargs.get("reply_markup", None)		#aka buttons {}
		if reply_markup:
			reply_markup = json.dumps(reply_markup)
		
		values = {
					"chat_id": str(chat_id),
					"text": text,
					"parse_mode": parse_mode,
					"disable_web_page_preview": disable_web_page_preview,
					"disable_notification": disable_notification,
					"reply_to_message_id": reply_to_message_id,
					
					"reply_markup": reply_markup,
				}
		return(self.method('sendMessage', values = values))
		
		
	def method(self, method, values = None):
	
		""" Вызов метода API
		:param method: название метода 		:type method: str
		:param values: параметры			:type values: dict
		"""

		values = values.copy() if values else {}

		with self.lock:
			# Ограничение 3 запроса в секунду
			delay = self.RPS_DELAY - (time() - self.last_request)
			if delay > 0:
				sleep(delay)

			try:
				response = self.http.post(self.cmd[method], values)
			except:
				print('NOT connect to telegram, change proxy')
				return False
				
			self.last_request = time()

		if response.ok:
			tx = response.json()
			if 'error' in tx:
				pprint(tx["error"])
				return False
			return(tx["result"])
		else:
			print('error')
			pprint(response)
			return False
		
	##### ##### ##### ##### #####

		
class Menu():

	files = {
				"state_main": 'menu.json',
				"state_bak": 'menu.bak',
				}
	msg = {
			"json_load": 'load state menu ok',
			"bak_load": 'load state menu bak ok',
			"new": 'genesis state menu ok',
			"save_start": 'save state',
			"save_end": 'end save state',
			}

	default	= {
				"intro": 'Добро пожаловать в меня бота',
				}
			

	def __init__(self, menu, commands, bot):
	
		self.state = menu
		self.generate_buttons()
		self.commands = commands
		self.tg = bot
		self.load()
		
		
	def resolve(self, message):

		user_id = str(message["chat"]["id"])
		body = message["text"]
		
		self.users_tg.setdefault(user_id, {"level": 'start'})
		level = self.users_tg[user_id]["level"]
		to_level = level
		print(level, user_id, body)
		
		flag = False
		for action in self.state[ self.users_tg[user_id]["level"] ]["action"]:
		
			# Если была нажата кнопка из подменю
			if action["label"] == body:
			
				# Сообщение от бота которое генерируется при нажатии на кнопку
				message_bot = action["message"]
			
				# Подгружаем функцию, если ее надо выполнить при нажатии кнопки, а не просто перейти на другой уровень
				cmd = self.commands.get(level + ':' + body, None)
				
				# Если есть указание перейти на другой уровень, иначе остаемся там где есть
				to_level = action.get("to_level", to_level)
				
				# Подгружаем клавиатуру
				keyboard = self.state[to_level]["keyboard"]
				
				flag = True
				break
				
		if flag:
			# Кнопка из под меню была нажата, отправляем сообщение
			self.tg.send_message(user_id, message_bot, reply_markup = keyboard)
			if cmd:
				# Исполнить функцию, так как нажата кнопка
				cmd(message)
		else:
			# Определяем нужно ли что-то сделать если кнопка не нажата, а что-то введено
			cmd = self.commands.get(level, None)
			to_level = self.state[level].get("to_level", to_level)
			if cmd:
				# Исполнить функцию, если не нажата ни одна кнопка, а введено что то иное
				cmd(message)
			else:
				# Откатиться на начало в случае бабуйни от пользователя
				to_level = 'start'
				self.tg.send_message(user_id, self.default["intro"], reply_markup = self.state["setdefault"]["keyboard"])
				
		if level != to_level:
			# Произошло изменение уровня пользователя
			self.users_tg[user_id]["level"] = to_level
			self.save()

	##### ##### ##### ##### #####
	
	def load(self):
		try:
			with open(self.files["state_main"], 'r', encoding = 'utf8') as f:
				self.users_tg = json.load(f)
				print(self.msg["json_load"])
		except:
			# not exist or bad file, load copy in *.bak
			try:
				with open(self.files["state_bak"], 'r', encoding = 'utf8') as f:
					self.users_tg = json.load(f)
					print(self.msg["bak_load"])
			except:
				# not exist or bad file, generate new dict
				self.users_tg = {}
				print(self.msg["new"])
	
	def save(self):
		print(self.msg["save_start"])
		with open(self.files["state_main"], 'w', encoding = 'utf8') as f:
			json.dump(self.users_tg, f, ensure_ascii = False)
		with open(self.files["state_bak"], 'w', encoding = 'utf8') as f:
			json.dump(self.users_tg, f, ensure_ascii = False)
		print(self.msg["save_end"])
		
	def generate_buttons(self):
	
		for level, values in self.state.items():
			buttons = [[]]
			n = 0
			for value in values["action"]:
				buttons[n].append({"text": value["label"]})
				row = value.get("row", False)
				if row:
					n += 1
					buttons.append([])
				
			self.state[level]["keyboard"] = {"keyboard": buttons, "resize_keyboard": True, "one_time_keyboard": True}
			
	##### ##### ##### ##### #####
		

