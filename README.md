# thallid-tg - Unofficial Python Library for Telegram

Thallid-Telegram библиотека для Telegram


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
