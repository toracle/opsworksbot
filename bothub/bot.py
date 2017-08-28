# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function, unicode_literals)

from bothub_client.bot import BaseBot


class Bot(BaseBot):
    def handle_message(self, event, context):
        # set access token
        # set secret token
        # set stack id
        # list instances
        # list layers
        # deploy
        # add instance

        content = event.get('content')

        if content == '/set credentials':
            self.start_slot_filling('credentials')
            return

        self.send_message('Echo: {}'.format(event['content']))

    def fill_slot(self, name):
        pass

    def is_slot_filling(self):
        pass

    
        
    def set_credentials(self, access_token, secret_token):
        pass


class SlotFiller(object):
    def __init__(self, storage, slot_definition):
        self.storage = storage
        self.slot_definition = slot_definition

    def fill_slot_set(self, name):
        if name not in self.slot_definition:
            raise Exception()

        data = self.storage.get_user_data()
        data.setdefault('_current_filling_slot_set', name)
        remaining_slot = data.setdefault('_remaining_slot', self.slot_definition)
