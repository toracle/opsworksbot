# -*- coding: utf-8 -*-

import json
import logging
from collections import namedtuple

import pytest
from bothub.intent import Intent
from bothub.intent import IntentResult
from bothub.intent import Slot
from bothub.intent import IntentState
from bothub.intent import NoSlotRemainsException
from bothub.dispatcher import DefaultDispatcher


Executed = namedtuple('Executed', ['command', 'args'])

class MockBot:
    def __init__(self):
        self.data = {}
        self.executed = []
        self.sent = []

    def get_user_data(self):
        return self.data

    def set_user_data(self, data):
        data_json_str = json.dumps(data)
        json_data = json.loads(data_json_str)
        self.data.update(**json_data)

    def on_default(self, *args):
        self.executed.append(Executed('on_default', args))

    def send_message(self, message):
        self.sent.append(message)

    def set_credentials(self, app_id, app_secret):
        self.executed.append(Executed('set_credentials', (app_id, app_secret)))


def fixture_intent_slots():
    return [
        Intent('credentials', 'set_credentials', [
            Slot('app_id', 'Please tell me your app ID', 'string'),
            Slot('app_secret', 'Please tell me your app secret', 'string'),
        ]),
        Intent('address', 'set_address', [
            Slot('country', 'Please tell me your country', 'string'),
            Slot('city', 'Please tell me your city', 'string'),
            Slot('road', 'Please tell me your road address', 'string'),
        ])
    ]


def test_init_intent_should_set_init_entries():
    bot = MockBot()
    intent_slots = fixture_intent_slots()
    state = IntentState(bot, intent_slots)
    state.init('credentials')
    assert bot.data['_intent_id'] == 'credentials'
    assert bot.data['_remaining_slots'] == [
        {'id': 'app_id', 'question': 'Please tell me your app ID', 'datatype': 'string'},
        {'id': 'app_secret', 'question': 'Please tell me your app secret', 'datatype': 'string'},
    ]


def test_get_result_should_return_result_with_next_message():
    bot = MockBot()
    intent_slots = fixture_intent_slots()
    state = IntentState(bot, intent_slots)
    state.init('credentials')
    assert bot.data['_remaining_slots'] == [
        {'id': 'app_id', 'question': 'Please tell me your app ID', 'datatype': 'string'},
        {'id': 'app_secret', 'question': 'Please tell me your app secret', 'datatype': 'string'},
    ]

    result = state.next()
    assert result.completed is False
    assert result.next_message == 'Please tell me your app ID'
    assert bot.data['_remaining_slots'] == [
        {'id': 'app_secret', 'question': 'Please tell me your app secret', 'datatype': 'string'},
    ]

    result = state.next({'content': '<my app ID>'})
    assert result.completed is False
    assert result.next_message == 'Please tell me your app secret'
    assert bot.data['_remaining_slots'] == []
    assert result.answers == {
        'app_id': '<my app ID>'
    }

    result = state.next({'content': '<my app secret>'})
    assert result.completed is True
    assert result.next_message is None
    assert result.answers == {
        'app_id': '<my app ID>',
        'app_secret': '<my app secret>'
    }


def test_get_result_should_raise_exception_when_exceeded_slots():
    bot = MockBot()
    intent_slots = fixture_intent_slots()
    state = IntentState(bot, intent_slots)
    state.init('credentials')
    state.next()
    state.next()
    state.next()

    with pytest.raises(NoSlotRemainsException):
        state.next()


def test_dispatch_should_execute_default():
    bot = MockBot()
    intent_slots = fixture_intent_slots()
    state = IntentState(bot, intent_slots)
    dispatcher = DefaultDispatcher(bot, state)
    dispatcher.dispatch({'content': 'hello'}, None)
    assert len(bot.executed) == 1
    executed = bot.executed.pop(0)
    assert executed == Executed(
        'on_default',
        ({'content': 'hello'}, None)
    )


def test_dispatch_should_execute_credentials():
    logging.basicConfig(level=logging.DEBUG)
    bot = MockBot()
    intent_slots = fixture_intent_slots()
    state = IntentState(bot, intent_slots)
    dispatcher = DefaultDispatcher(bot, state)
    dispatcher.dispatch({'content': '/intent credentials'}, None)
    dispatcher.dispatch({'content': 'my token'}, None)
    dispatcher.dispatch({'content': 'my secret token'}, None)
    assert len(bot.executed) == 1
    executed = bot.executed.pop(0)
    assert executed == Executed('set_credentials', ('my token', 'my secret token'))


def test_dispatch_should_trigger_intent_and_default():
    logging.basicConfig(level=logging.DEBUG)
    bot = MockBot()
    intent_slots = fixture_intent_slots()
    state = IntentState(bot, intent_slots)
    dispatcher = DefaultDispatcher(bot, state)
    dispatcher.dispatch({'content': '/intent credentials'}, None)
    dispatcher.dispatch({'content': 'my token'}, None)
    dispatcher.dispatch({'content': 'my secret token'}, None)
    dispatcher.dispatch({'content': 'hello'}, None)
    assert len(bot.executed) == 2
    executed = bot.executed.pop(0)
    assert executed == Executed('set_credentials', ('my token', 'my secret token'))
    executed = bot.executed.pop(0)
    assert executed == Executed('on_default', ({'content': 'hello'}, None))
