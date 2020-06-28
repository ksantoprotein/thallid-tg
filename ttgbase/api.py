# -*- coding: utf-8 -*-

import requests
import threading
import json

from time import time, sleep
from pprint import pprint

from .rpc_client import RpcClient

#https://core.telegram.org/bots/api


class Api(object):

	BOT_WAIT = 1
	limit = 10			# кол во сообщий для бота в апдейте
	DEL_DELAY = 25		# удаляем сообщения бота по умолчанию через 25 секунд
	
	bot_commands = ['private_text', 'chat_text', 'private_reply', 'chat_reply', 'private_entities', 'chat_entities']
	#bot_cmd_list = ['getMe', 'getUpdates', 'getChat', 'getFile', 'sendMessage', 'sendPhoto', 'sendAnimation', 'sendVideo', 'sendMediaGroup', 'deleteMessage']
					
	ext_types = {"mp4": 'video', "gif": 'video', "jpg": 'photo', "png": 'photo'}
	cmd_types = {"video": 'sendVideo', "animation": 'sendAnimation', "photo": 'sendPhoto'}
	
	
	def __init__(self, token, **kwargs):
	
		self.token = token
		report = kwargs.pop("report", False)
		PROXY = kwargs.pop("PROXY", False)
		self.rpc = RpcClient(self.token, report=report, PROXY=PROXY)
		
		self.load_state()
		self.prepare_commands_empty()
	
		print('check BOT telegram')
		tx = self.get_me()
		if tx:
			self.bot_name = tx["username"]
			print(self.bot_name, 'ok')
		else:
			print('ERROR', token)
			input('STOP')
		
	##### ##### MESSAGE ##### #####
		
	def send_message(self, chat_id, text, **kwargs):
		
		parse_mode = kwargs.get("parse_mode", None)
		disable_web_page_preview = kwargs.get("disable_web_page_preview", None)
		disable_notification = kwargs.get("disable_notification", None)
		reply_to_message_id = kwargs.get("reply_to_message_id", None)
		
		reply_markup = kwargs.get("reply_markup", None)		#aka buttons {}
		if reply_markup: reply_markup = json.dumps(reply_markup)
		
		values = {
					"chat_id": str(chat_id),
					"text": text,
					"parse_mode": parse_mode,
					"disable_web_page_preview": disable_web_page_preview,
					"disable_notification": disable_notification,
					"reply_to_message_id": reply_to_message_id,
					"reply_markup": reply_markup,
				}
				
		flag_error = False
		try:
			tx = self.rpc.call('sendMessage', **values)
		except:
			print('error to send message')
			flag_error = True
			tx = None
		
		### delete message
		delete_message = kwargs.get("delete", False)
		if delete_message and not(flag_error):
			# Задержка перед удалением мессаги 25 секунд
			dt = kwargs.get("time", self.DEL_DELAY)
			try:
				payload = [str(tx["chat"]["id"]), tx["message_id"], dt]
				tx_del = self.delete_message(payload)
			except:
				print('error to del message')
		
		return tx
		
	def delete_message(self, payload, **kwargs):
		bot_thread_del_msg = threading.Thread(target=self._delete_message, daemon=True, args=(payload,))
		bot_thread_del_msg.start()
		return True
		
	def _delete_message(self, payload, **kwargs):
		chat_id, message_id, dt = payload
		sleep(dt)
		try:
			tx = self.rpc.call('deleteMessage', chat_id=int(chat_id), message_id=message_id)
		except:
			tx = False
			print('error delete msg')
		return tx
		
	##### ##### GET ##### #####
	
	def get_me(self):
		return(self.rpc.call('getMe'))

	def getChat(self, chat_id):
		return(self.rpc.call('getChat', values={"chat_id": chat_id}))
		
	def get_updates(self):
		return(self.rpc.call('getUpdates'))
		
	def get_updates_limit(self):
		return(self.rpc.call('getUpdates', offset=self.state["offset"], limit=self.limit))
		
	def getFile(self, file_id):
		return(self.rpc.call('getFile', file_id=file_id))

	##### ##### STATE ##### #####
	
	def load_state(self):
		try:
			with open('state.json', 'r', encoding='utf8') as f:
				self.state = json.load(f)
			if self.state["token"] != self.token: self.prepare_state()
		except:	# not exist or bad file
			self.prepare_state()
		
	def save_state(self):
		with open('state.json', 'w', encoding='utf8') as f:
			json.dump(self.state, f, ensure_ascii=False)
			
	def prepare_state(self):
		self.state = {"token": self.token, "offset": 0}
		self.save_state()
		
	def prepare_commands_empty(self):
		self.commands = {cmd: self.command_pass for cmd in self.bot_commands}
	
	
	##### ##### LOOP ##### #####
	
	def run(self):
	
		# self.commands функции которые надо вызвать на новые сообщения
		self.flag = True
		bot_thread = threading.Thread(target=self.scan, daemon=True)
		bot_thread.start()

		
	def scan(self):
	
		# Необходимо загрузить функции commands
	
		while self.flag:

			updates = self.get_updates_limit()		# Считываем тока по одному сообщению (это замедляет бота, так что далее нужна оптимизация)
			for tx in updates:
			
				#pprint(tx)
				
				message = tx.get("message", None)
				edited = False if message else True
				#print(message)
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
						#pprint(tx)
						print('new message')
						
				else:
					print('not message')
					#pprint(tx)
				
				self.state["offset"] = tx["update_id"] + 1
				self.save_state()
				#input('next')
	
			#sleep(self.RPS_DELAY)		### так же задействовать таймер сообщений, чтобы асинхронные запросы пахали
			sleep(self.BOT_WAIT)
			
			
	def command_pass(self, message):
		print('not used')
		pass

		
	"""
	def send_media(self, chat_id, data, **kwargs):
	
		caption = kwargs.get("caption", None)
		data = [data] if isinstance(data, str) else data
		mono = True if len(data) == 1 else False
		values = {"chat_id": str(chat_id)}
		url = kwargs.get("url", None)
		
		files, media = {}, []
		if mono:
			ext = data[0].split('.')[-1:][0].lower()
			type = self.ext_types[ext]
			cmd = self.cmd_types[type]
			values["caption"] = caption
			if url:
				values[type] = data[0]
			else:
				with open(data[0], 'rb') as f:
					files[type] = f.read()
			if type == 'video':
				values["supports_streaming"] = True
			
		else:
			cmd = 'sendMediaGroup'
			for link in data:
				ext = link.split('.')[-1:][0].lower()
				type = self.ext_types[ext]
				payment = {"type": type}
				sleep(0.001)
				if url:
					payment["media"] = link
				else:
					name = str(round(time() * 1000))
					with open(link, 'rb') as f:
						files[name] = f.read()
					payment["media"] = 'attach://' + name
				if type == 'video':
					payment["supports_streaming"] = True
				if type == 'animation':
					payment["type"] = 'photo'
				
				media.append(payment)
					
			values["media"] = json.dumps(media)
			
		files = None if url else files
		
		try:
			tx = self.method(cmd, values = values, files = files)
		except:
			print('error to send message')
			tx = None
		
		return tx
	"""

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

	default	= {"intro": {"Russian": 'Добро пожаловать в меню бота', "English": 'Welcome to the bot menu'}}
			

	def __init__(self, menu, commands, bot):
	
		self.state = menu
		self.generate_buttons()
		self.commands = commands
		self.tg = bot
		self.load()
		
		
	def resolve(self, message):

		user_id = str(message["chat"]["id"])
		body = message["text"]
		
		self.users_tg.setdefault(user_id, {"level": 'start', "payload": {}})		# add payload
		level = self.users_tg[user_id]["level"]
		to_level = level
		lng = self.users_tg[user_id].get("language", 'Russian')
		
		print(level, user_id, body, lng)
		
		flag = False
		for action in self.state[ self.users_tg[user_id]["level"] ]["action"]:
		
			# Если была нажата кнопка из подменю
			if action["label"] == body:
			
				# Сообщение от бота которое генерируется при нажатии на кнопку
				message_bot = action["message"].get(lng, action["message"])
			
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
			self.tg.send_message(user_id, message_bot, reply_markup=keyboard)
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
				self.tg.send_message(user_id, self.default["intro"][lng], reply_markup = self.state["setdefault"]["keyboard"])
				
		if level != to_level:
			# Произошло изменение уровня пользователя
			self.users_tg[user_id]["level"] = to_level
			self.save()

	##### ##### ##### ##### #####
	
	def load(self):
		try:
			with open(self.files["state_main"], 'r', encoding='utf8') as f:
				self.users_tg = json.load(f)
				print(self.msg["json_load"])
		except:
			# not exist or bad file, load copy in *.bak
			try:
				with open(self.files["state_bak"], 'r', encoding='utf8') as f:
					self.users_tg = json.load(f)
					print(self.msg["bak_load"])
			except:
				# not exist or bad file, generate new dict
				self.users_tg = {}
				print(self.msg["new"])
	
	def save(self):
		#print(self.msg["save_start"])
		with open(self.files["state_main"], 'w', encoding='utf8') as f:
			json.dump(self.users_tg, f, ensure_ascii=False)
		with open(self.files["state_bak"], 'w', encoding='utf8') as f:
			json.dump(self.users_tg, f, ensure_ascii=False)
		#print(self.msg["save_end"])
		
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
		
