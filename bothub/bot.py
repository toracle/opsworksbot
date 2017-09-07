# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function, unicode_literals)

import os
import boto3

from bothub_client.bot import BaseBot
from bothub_client.messages import Message


class Bot(BaseBot):
    def on_default(self, event, context):
        self.send_message("I can't understand it.")
        self.on_help(event, context)

    def on_stacks(self, event, context):
        data = self.get_user_data()
        client = self.get_boto_client(data)

        response = client.describe_stacks()
        stacks = [(s['StackId'], s['Name']) for s in response['Stacks']]

        message = Message(event)
        message.set_text('Select one stack:')
        for stack in stacks:
            message.add_postback_button(stack[1], '/use_stack {} {}'.format(stack[0], stack[1]))
        self.send_message(message)

    def on_use_stack(self, event, context, stack_id, stack_name):
        data = self.get_user_data()
        data['stack_id'] = stack_id
        self.set_user_data(data)

        message = Message(event)
        message.set_text('Use stack {} now'.format(stack_name))
        message.add_postback_button('Show layers', '/layers')
        self.send_message(message)

    def on_layers(self, event, context):
        data = self.get_user_data()
        stack_id = data['stack_id']
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
        client = self.get_boto_client(data)

        response = client.describe_layers(LayerIds=[layer_id])
        layer = response['Layers'][0]

        instances = client.describe_instances(LayerId=layer_id)['Instances']
        text_lines = ['Layer [{Name}]'.format(**layer), '']

        for instance in instances:
            text_lines.append('* {Hostname} is {Status}'.format(**instance))

        message_text = '\n'.join(text_lines)
        message = Message(event)
        message.set_text(message_text)
        self.send_message(message)

    def on_deploy(self, event, context):
        data = self.get_user_data()
        stack_id = data['stack_id']
        client = self.get_boto_client(data)

        response = client.describe_apps(StackId=stack_id)
        apps = [(a['AppId'], a['Name']) for a in response['Apps']]
        message = Message(event)
        message.set_text('Select an app to deploy:')
        for app in apps:
            message.add_postback_button(app[1], '/deploy_app {}'.format(app[0]))
        self.send_message(message)

    def on_deploy_app(self, event, context, app_id):
        message = Message(event)
        message.set_text('Which deploy command do you want to execute?')
        for command in ['deploy', 'update_custom_cookbook']:
            message.add_quick_reply(command, '/deploy_app_do_command {} {}'.format(app_id, command))
        self.send_message(message)

    def on_deploy_app_do_command(self, event, context, app_id, command):
        data = self.get_user_data()
        stack_id = data['stack_id']
        client = self.get_boto_client(data)

        response = client.create_deployment(
            StackId=stack_id,
            AppId=app_id,
            Command={'Name': command}
        )

        message = Message(event)
        message.set_text('Deployment is started')
        message.add_postback_button('Deployment status', '/deploy_status {}'.format(response['DeploymentId']))
        self.send_message(message)

    def on_deploy_status(self, event, context, deploy_id):
        data = self.get_user_data()
        client = self.get_boto_client(data)

        response = client.describe_deployments(DeploymentIds=[deploy_id])
        deploy = response['Deployments'][0]

        message = Message(event)
        message.set_text('Deployment is {Status}'.format(**deploy))
        if deploy['Status'] == 'running':
            message.add_quick_reply('Deployment status', '/deploy_status {}'.format(deploy_id))
        else:
            message.add_quick_reply('Layer list', '/layers')
            message.add_quick_reply('Deploy', '/deploy')
        self.send_message(message)

    def on_help(self, event, context):
        message = Message(event)
        message.set_text('Let me tell you what can I do.')
        message.add_postback_button('Stack List', '/stacks')
        message.add_postback_button('Layer List', '/layers')
        message.add_postback_button('Deploy', '/deploy')
        self.send_message(message)

    def on_start(self, event, context):
        message = Message(event)
        message.set_text('\n'.join(
            [
                "Hello, I'm OpsworksBot.",
                '',
                'I help you to manage Opsworks with ease. You can navigate stacks and layers, execute a deployment with me.',
                '',
                'To let me work, you need to tell me your access-key and secret-access-key which has a proper permission on Opsworks',
            ]
        ))
        message.add_quick_reply("Yes, I'll tell you my credentials", '/intent credentials')
        message.add_quick_reply("No, thanks")
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

    def set_credentials(self, event, context, access_token, secret_access_token):
        data = self.get_user_data()
        data['credentials'] = {
            'aws_access_key_id': access_token,
            'aws_secret_access_key': secret_access_token,
        }
        self.set_user_data(data)
        self.send_message('Now I can manage your Opsworks stacks.')
        self.on_help(event, context)
