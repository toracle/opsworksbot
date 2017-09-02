# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function, unicode_literals)

import boto3

from bothub_client.bot import BaseBot
from bothub_client.messages import Message

from bothub.intent import IntentState
from bothub.intent import Intent
from bothub.intent import Slot
from bothub.dispatcher import DefaultDispatcher


class Bot(BaseBot):
    def handle_message(self, event, context):
        content = event.get('content')

        intent_slots = [
            Intent('credentials', 'set_credentials', [
                Slot('access_token', 'Please tell me your access token', 'string'),
                Slot('secret_access_token', 'Please tell me your secret access token', 'string'),
                Slot('stack_id', 'Please tell me your stack_id', 'string')
            ])
        ]

        state = IntentState(self, intent_slots)
        dispatcher = DefaultDispatcher(self, state)
        dispatcher.dispatch(event, context)

    def on_default(self, event, context):
        self.send_message('Echo: {}'.format(event['content']))

    def on_layers(self, event, context):
        data = self.get_user_data()
        stack_id = data['credentials']['stack_id']
        client = self.get_boto_client(data)
        response = client.describe_layers(StackId=stack_id)
        layers = [(l['LayerId'], l['Name']) for l in response['Layers']]
        message = Message(event)
        message.set_text('Layer list:')
        for layer in layers:
            message.add_postback_button(layer[1], '/layer {}'.format(layer[0]))
        self.send_message(message)

    def on_layer(self, event, context, layer_id):
        data = self.get_user_data()
        stack_id = data['credentials']['stack_id']
        client = self.get_boto_client(data)
        response = client.describe_layers(LayerIds=[layer_id])
        layer = response['Layers'][0]
        message_text = '''Layer [{Name}]'''.format(**layer)
        message = Message(event)
        message.set_text(message_text)
        message.add_postback_button('Instances', '/layer_instances {}'.format(layer_id))
        message.add_postback_button('Add instance', '/add_instance {}'.format(layer_id))
        self.send_message(message)

    def on_layer_instances(self, event, context, layer_id):
        data = self.get_user_data()
        stack_id = data['credentials']['stack_id']
        client = self.get_boto_client(data)

        response = client.describe_layers(StackId=stack_id)
        layer = response['Layers'][0]

        instances = client.describe_instances(LayerId=layer_id)['Instances']
        text_lines = []
        text_lines.append('Instances of Layer {Name}'.format(**layer))
        text_lines.append('')
        for instance in instances:
            text_lines.append('{Hostname} is {Status}'.format(**instance))
        message = Message(event)
        message.set_text('\n'.join(text_lines))
        message.add_postback_button('Add instance', '/add_instance {LayerId}'.format(**layer))
        self.send_message(message)

    def get_boto_client(self, data):
        credentials = data['credentials']
        kwargs = {
            'aws_access_key_id': credentials['aws_access_key_id'],
            'aws_secret_access_key': credentials['aws_secret_access_key'],
            'region_name': 'us-east-1'
        }
        client = boto3.client('opsworks', **kwargs)
        return client

    def set_credentials(self, access_token, secret_access_token, stack_id):
        data = self.get_user_data()
        data['credentials'] = {
            'aws_access_key_id': access_token,
            'aws_secret_access_key': secret_access_token,
            'stack_id': stack_id,
        }
        self.set_user_data(data)
