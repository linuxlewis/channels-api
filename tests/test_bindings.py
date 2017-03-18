import json

from django.utils.encoding import force_text
from django.contrib.auth.models import User
from rest_framework import serializers

from channels.message import pending_message_store
from channels.tests import ChannelTestCase, Client

from channels_api import bindings, permissions
from channels_api.settings import api_settings

from .models import TestModel


class TestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestModel
        fields = ('id', 'name')


class TestModelResourceBinding(bindings.ResourceBinding):

    model = TestModel
    queryset = TestModel.objects.all()
    serializer_class = TestModelSerializer
    stream = 'testmodel'


class TestPermissionResourceBinding(bindings.ResourceBinding):

    model = TestModel
    queryset = TestModel.objects.all()
    serializer_class = TestModelSerializer
    permission_classes = (permissions.IsAuthenticated, )
    stream = 'testmodel'


class ResourceBindingTestCase(ChannelTestCase):

    def setUp(self):
        super(ResourceBindingTestCase, self).setUp()
        self.client = Client()

    def _send_and_consume(self, channel, data):
        """Helper that sends and consumes message and returns the next message."""
        self.client.send_and_consume(force_text(channel), data)
        return self._get_next_message()

    def _get_next_message(self):
        msg = self.client.get_next_message(self.client.reply_channel)
        try:
            return json.loads(msg['text'])
        except Exception:
            return None

    def _build_message(self, stream, payload):
        return {"text": json.dumps({"stream": stream, "payload": payload}), "path": "/"}

    def _build_authentication(self, username, password):
        return {"username": username, "password": password, "text": "", "path": "/"}

    def test_create(self):
        """Integration that asserts routing a message to the create channel.

        Asserts response is correct and an object is created.
        """
        json_content = self._send_and_consume("websocket.receive", self._build_message("testmodel", {
            'action': 'create',
            'pk': None,
            'request_id': 'client-request-id',
            'data': {'name': 'some-thing'}
        }))
        # it should create an object
        self.assertEqual(TestModel.objects.count(), 1)

        expected = {
            'action': 'create',
            'data': TestModelSerializer(TestModel.objects.first()).data,
            'errors': [],
            'request_id': 'client-request-id',
            'response_status': 201
        }
        # it should respond with the serializer.data
        self.assertEqual(json_content['payload'], expected)

    def test_create_failure(self):
        """Integration that asserts error handling of a message to the create channel."""

        json_content = self._send_and_consume('websocket.receive', self._build_message("testmodel", {
            'action': 'create',
            'pk': None,
            'request_id': 'client-request-id',
            'data': {},
        }))
        # it should not create an object
        self.assertEqual(TestModel.objects.count(), 0)

        expected = {
            'action': 'create',
            'data': None,
            'request_id': 'client-request-id',
            'errors': [{'name': ['This field is required.']}],
            'response_status': 400
        }
        # it should respond with an error
        self.assertEqual(json_content['payload'], expected)

    def test_delete(self):
        instance = TestModel.objects.create(name='test-name')

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'delete',
            'pk': instance.id,
            'request_id': 'client-request-id',
        }))

        expected = {
            'action': 'delete',
            'errors': [],
            'data': {},
            'request_id': 'client-request-id',
            'response_status': 200
        }
        self.assertEqual(json_content['payload'], expected)
        self.assertEqual(TestModel.objects.count(), 0)

    def test_delete_failure(self):
        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'delete',
            'pk': -1,
            'request_id': 'client-request-id'
        }))

        expected = {
            'action': 'delete',
            'errors': ['Not found.'],
            'data': None,
            'request_id': 'client-request-id',
            'response_status': 404
        }

        self.assertEqual(json_content['payload'], expected)

    def test_list(self):
        for n in range(api_settings.DEFAULT_PAGE_SIZE + 1):
            TestModel.objects.create(name='Name-{}'.format(str(n)))

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'list',
            'request_id': 'client-request-id',
            'data': None,
        }))

        self.assertEqual(len(json_content['payload']['data']), api_settings.DEFAULT_PAGE_SIZE)

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'list',
            'request_id': 'client-request-id',
            'data': {
                'page': 2
            }
        }))

        self.assertEqual(len(json_content['payload']['data']), 1)
        self.assertEqual('client-request-id', json_content['payload']['request_id'])

    def test_retrieve(self):

        instance = TestModel.objects.create(name="Test")

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'retrieve',
            'pk': instance.id,
            'request_id': 'client-request-id'
        }))
        expected = {
            'action': 'retrieve',
            'data': TestModelSerializer(instance).data,
            'errors': [],
            'response_status': 200,
            'request_id': 'client-request-id'
        }
        self.assertTrue(json_content['payload'] == expected)

    def test_retrieve_404(self):
        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'retrieve',
            'pk': 1,
            'request_id': 'client-request-id'
        }))
        expected = {
            'action': 'retrieve',
            'data': None,
            'errors': ['Not found.'],
            'response_status': 404,
            'request_id': 'client-request-id'
        }
        self.assertEqual(json_content['payload'], expected)

    def test_retrieve_invalid_pk_404(self):
        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'retrieve',
            'pk': 'invalid-pk-value',
            'request_id': 'client-request-id'
        }))
        expected = {
            'action': 'retrieve',
            'data': None,
            'errors': ['Not found.'],
            'response_status': 404,
            'request_id': 'client-request-id'
        }
        self.assertEqual(json_content['payload'], expected)

    def test_subscribe(self):

        json_content = self._send_and_consume('websocket.receive', self._build_message("testmodel",{
            'action': 'subscribe',
            'data': {
                'action': 'create'
            },
            'request_id': 'client-request-id'
        }))

        expected_response = {
            'action': 'subscribe',
            'request_id': 'client-request-id',
            'data': {
                'action': 'create'
             },
            'errors': [],
            'response_status': 200
        }

        self.assertEqual(json_content['payload'], expected_response)

        # it should be on the create group
        instance = TestModel.objects.create(name='test-name')

        expected = {
            'action': 'create',
            'data': TestModelSerializer(instance).data,
            'model': 'tests.testmodel',
            'pk': instance.id
        }

        actual = self._get_next_message()

        self.assertEqual(expected, actual['payload'])

    def test_subscribe_failure(self):

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'subscribe',
            'data': {
            },
            'request_id': 'client-request-id'
        }))

        expected = {
            'action': 'subscribe',
            'data': None,
            'errors': ['action required'],
            'request_id': 'client-request-id',
            'response_status': 400
        }
        self.assertEqual(expected, json_content['payload'])

    def test_update(self):
        instance = TestModel.objects.create(name='some-test')

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
            'action': 'update',
            'pk': instance.id,
            'data': {'name': 'some-value'},
            'request_id': 'client-request-id'
        }))

        instance.refresh_from_db()

        expected = {
            'action': 'update',
            'errors': [],
            'data': TestModelSerializer(instance).data,
            'response_status': 200,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    def test_update_failure(self):
        instance = TestModel.objects.create(name='some-test')

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', {
            'action': 'update',
            'pk': -1,
            'data': {'name': 'some-value'},
            'request_id': 'client-request-id'
        }))

        expected = {
            'data': None,
            'action': 'update',
            'errors': ['Not found.'],
            'response_status': 404,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    def test_no_permission(self):
        instance = TestModel.objects.create(name='some-test')

        """Simulating the connection opening"""
        self._send_and_consume('websocket.connect', {"text": json.dumps({}), "path": "/"})

        json_content = self._send_and_consume('websocket.receive', self._build_message('user:testmodel',{
            'action': 'update',
            'pk': instance.id,
            'data': {'name': 'some-value'},
            'request_id': 'client-request-id'
        }))

        expected = {
            'data': None,
            'action': 'update',
            'errors': ['Permission Denied'],
            'response_status': 401,
            'request_id': None
        }

        self.assertEqual(json_content['payload'], expected)

    def test_permission(self):
        instance = TestModel.objects.create(name='some-test')

        User.objects.create_user('john', 'john@snowmanlabs.com', 'johnpassword')

        """Simulating the connection opening by sending username and password """
        self._send_and_consume('websocket.connect', self._build_authentication('john', 'johnpassword'))

        json_content = self._send_and_consume('websocket.receive', self._build_message('user:testmodel',{
            'action': 'update',
            'pk': instance.id,
            'data': {'name': 'some-value'},
            'request_id': 'client-request-id'
        }))

        """Simulating the disconnection opening """
        self._send_and_consume('websocket.disconnect', self._build_authentication('', ''))

        instance.refresh_from_db()

        expected = {
            'action': 'update',
            'errors': [],
            'data': TestModelSerializer(instance).data,
            'response_status': 200,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)


