#!/usr/bin/python

from TelegramBotWrapper import TBot
from Update import TextMessage, CallbackQuery, LocationMessage
import requests

class BusBot(TBot):
	def __init__(self):
		super(BusBot, self).__init__()
		self.Update = None
		self.currentUpdate = None


	def processTextMessage(self, currentUpdate):
		TextUpdate = TextMessage() #instantiate Update Object, might have to separate them into smaller objects that composes into a whole Upd$
		TextUpdate.Message_ID = currentUpdate['message']['message_id']
		TextUpdate.From_ID = currentUpdate['message']['from']['id']
		TextUpdate.From_is_bot = currentUpdate['message']['from']['is_bot']
		TextUpdate.From_first_name = currentUpdate['message']['from']['first_name']
		if 'username' in currentUpdate['message']['from']:
			TextUpdate.From_username = currentUpdate['message']['from']['username']
		TextUpdate.From_language_code = currentUpdate['message']['from']['language_code']
		TextUpdate.Chat_ID = currentUpdate['message']['chat']['id']
		TextUpdate.Chat_first_name = self.remove_nonascii(currentUpdate['message']['chat']['first_name'])
		if 'username' in currentUpdate['message']['chat']:
			TextUpdate.Chat_username = currentUpdate['message']['chat']['username']
		TextUpdate.Chat_type = currentUpdate['message']['chat']['type']
		TextUpdate.Message_date = currentUpdate['message']['date']
		TextUpdate.Message_text = currentUpdate['message']['text']
		return TextUpdate


	def processCallbackQuery(self, currentUpdate):
		CallBackUpdate = CallbackQuery() #instantiate Update Object, might have to separate them into smaller objects that composes into a whole Upd$
		CallBackUpdate.Callback_Query_ID = currentUpdate['callback_query']['id']
		self.answerCallbackQuery(callback_query_id = CallBackUpdate.Callback_Query_ID) #answer callback asap
		CallBackUpdate.Message_ID = currentUpdate['callback_query']['message']['message_id']
		CallBackUpdate.From_ID = currentUpdate['callback_query']['message']['from']['id']
		CallBackUpdate.From_is_bot = currentUpdate['callback_query']['message']['from']['is_bot']
		CallBackUpdate.From_first_name = self.remove_nonascii(currentUpdate['callback_query']['message']['from']['first_name'])
		if 'username' in currentUpdate['callback_query']['message']['from']:
			CallBackUpdate.From_username = currentUpdate['callback_query']['message']['from']['username']
		CallBackUpdate.From_language_code = currentUpdate['callback_query']['from']['language_code']
		CallBackUpdate.Chat_ID = currentUpdate['callback_query']['message']['chat']['id']
		CallBackUpdate.Chat_first_name = self.remove_nonascii(currentUpdate['callback_query']['message']['chat']['first_name'])
		if 'username' in currentUpdate['callback_query']['message']['chat']:
			CallBackUpdate.Chat_username = currentUpdate['callback_query']['message']['chat']['username']
		CallBackUpdate.Chat_type = currentUpdate['callback_query']['message']['chat']['type']
		CallBackUpdate.Message_date = currentUpdate['callback_query']['message']['date']
		CallBackUpdate.Message_text = currentUpdate['callback_query']['message']['text']
		CallBackUpdate.Callback_chat_instance = currentUpdate['callback_query']['chat_instance']
		CallBackUpdate.Callback_Data = currentUpdate['callback_query']['data']
		return CallBackUpdate


	def processLocation(self, currentUpdate):
		LocationUpdate = LocationMessage()
		LocationUpdate.Chat_ID = currentUpdate['message']['chat']['id']
		LocationUpdate.Lat = str(currentUpdate['message']['location']['latitude'])
		LocationUpdate.Long = str(currentUpdate['message']['location']['longitude'])
		return LocationUpdate



	def remove_nonascii(self, s):
		return ''.join([i if ord(i) < 128 else ' ' for i in s])
