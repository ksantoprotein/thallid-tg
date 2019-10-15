# thallid-tg - Python Library for Telegram Bot

Thallid-Telegram библиотека для Telegram ботов


# Installation

https://github.com/ksantoprotein/thallid-tg.git

# Documentation


# Usage examples

#### Menu
``` python
from ttgbase.api import Api, Menu
import menu

token = '...'
tg = Api(token)

tg.commands["private_text"] = функция для обработки приватных сообщений
tg.commands["chat_text"] = функция для обработки сообщений в чатах

commands = {}

bot_menu = Menu(menu.menu, commands, tg)

tg.run()
```

# Подключеня следующие функции

getMe
getUpdates
sendMessage
deleteMessage
getChat

tg.send_message(chat_id, msg, delete = True)
