#!/usr/bin/python

class Message(object):
	def __init__(self):
		self.From_ID = None
		self.From_is_bot = None
		self.From_first_name = None
		self.From_username = None
		self.From_language_code = None
		self.Message_ID = None
		self.Chat_ID = None
		self.Chat_first_name = None
		self.Chat_username = None
		self.Chat_type = None
		self.Message_date = None
		self.Message_text = None



class TextMessage(Message):
	def __init__(self):
		pass


class LocationMessage(Message):
	def __init__(self):
		self.Lat = None
		self.Long = None


class CallbackQuery(Message):
	def __init__(self):
		self.Callback_Query_ID = None
		self.Callback_chat_instance = None
		self.Callback_Data = None





