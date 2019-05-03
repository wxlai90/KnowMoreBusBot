#!/usr/bin/python

#minimal/subset python wrapper of telegram bot api
#just enough for this bus bot

import requests
import logging
import json

logging.basicConfig(filename = './TBot.log', level = logging.DEBUG, filemode = 'w')
logger = logging.getLogger()

class TBot(object):
    def __init__(self):
        self.BOT_TOKEN = 'YOUR BOT TOKEN'
        self.baseurl = '{}{}/'.format('https://api.telegram.org/bot', self.BOT_TOKEN)
        logger.info('Baseurl is: {}'.format(self.baseurl))

    def sendTextMessage(self, **kargs):    #generalization?
        chat_id = kargs['chat_id']
        text = kargs['text']
        data = {}
        data['chat_id'] = chat_id
        data['text'] = text
        r = requests.post(self.baseurl + 'sendMessage', data = data)
        if r.status_code != 200:
            logger.warning('sendTextMessage returned: {}'.format(r.status_code))
        else:
            logger.info('sendTextMessage returned: OK')


    def sendHTMLMessage(self, **kargs):    #generalization?
        chat_id = kargs['chat_id']
        text = kargs['text']
        data = {}
        data['chat_id'] = chat_id
        data['text'] = text
        data['parse_mode'] = 'HTML'
        r = requests.post(self.baseurl + 'sendMessage', data = data)
        if r.status_code != 200:
            logger.warning('sendTextMessage returned: {}'.format(r.status_code))
        else:
            logger.info('sendTextMessage returned: OK')



    def sendInlineKeyboard(self, **kargs):
        '''sends inline keyboard to user, fields required in kargs:
                chat_id (str)
                text (str)
                parse_mode (str) [optional] HTML/Markdown
                display_text (list)
                callback_data (list)
        '''

        headers = {
                'Content-Type': 'application/json'
                    }

        chat_id = kargs['chat_id']
        text = kargs['text']
        data = {}
        if 'parse_mode' in kargs:
            parse_mode = kargs['parse_mode']
            data['parse_mode'] = parse_mode
        display_text = kargs['display_text']
        callback_data_list = kargs['callback_data']
        inline_keyboard = self.constructInlineKeyboardButtons(display_text, callback_data_list)
        data['chat_id'] = chat_id
        data['text'] = text
        data['reply_markup'] = inline_keyboard
        data = json.dumps(data)
        r = requests.post(self.baseurl + 'sendMessage', headers = headers, data = data)
        if r.status_code != 200:
            logger.warning('sendInlineKeyboard returned: {}'.format(r.status_code))
        else:
            logger.info('sendInlineKeyboardreturned: OK')


    def editInlineKeyBoard(self, **kargs):
        '''sends inline keyboard to user, fields required in kargs:
                chat_id (str)
                text (str)
                message_id (str)
                parse_mode (str) [optional] HTML/Markdown
                display_text (list)
                callback_data (list)
        '''

        headers = {
                'Content-Type': 'application/json'
                    }

        chat_id = kargs['chat_id']
        text = kargs['text']
        message_id = kargs['message_id']
        data = {}
        if 'parse_mode' in kargs:
            parse_mode = kargs['parse_mode']
            data['parse_mode'] = parse_mode
        display_text = kargs['display_text']
        callback_data_list = kargs['callback_data']
        inline_keyboard = self.constructInlineKeyboardButtons(display_text, callback_data_list)
        data['chat_id'] = chat_id
        data['text'] = text
        data['message_id'] = message_id
        data['reply_markup'] = inline_keyboard
        data = json.dumps(data)
        r = requests.post(self.baseurl + 'editMessageText', headers = headers, data = data)
        if r.status_code != 200:
            logger.warning('editMessageText returned: {}'.format(r.status_code))
        else:
            logger.info('editMessageText returned: OK')

    def sendReplyKeyboard(self, **kargs):
        pass

    def removeReplyKeyboard(self, **kargs):
        pass


    def answerCallbackQuery(self, **kargs):
        callback_query_id = kargs['callback_query_id']
        data = {}
        data['callback_query_id'] = callback_query_id
        r = requests.post(self.baseurl + 'answerCallbackQuery', data = data)
        if r.status_code != 200:
            logger.warning('answerCallbackQuery returned: {}'.format(r.status_code))
        else:
            logger.info('answerCallbackQuery: OK')

    def constructInlineKeyboardButtons(self, buttons_text, buttons_callback_data):
        inline_keyboard = {"inline_keyboard": []}
        if len(buttons_text) != len(buttons_callback_data):
            return
        for i in range(0, len(buttons_text)):
            d = {}
            d['text'] = buttons_text[i]
            d['callback_data'] = buttons_callback_data[i]
            inline_keyboard["inline_keyboard"].append([d])
        return inline_keyboard
