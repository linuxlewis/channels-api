import pytest

import json

from channels.testing import ChannelsLiveServerTestCase

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from django.contrib.auth.models import User
from django.utils.encoding import force_text
from rest_framework import serializers

#from channels.test import WSClient
#from channels.tests import ChannelTestCase, Client

#from channels_api import bindings
#from channels_api.decorators import list_action, detail_action
#from channels_api.permissions import IsAuthenticated
#from channels_api.settings import api_settings

from .models import TestModel


class TestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestModel
        fields = ('id', 'name')

"""
class TestModelResourceBinding(bindings.ResourceBinding):

    model = TestModel
    queryset = TestModel.objects.all()
    serializer_class = TestModelSerializer
    stream = 'testmodel'

    @list_action()
    def test_list(self, data=None, **kwargs):
        return 'some data', 200

    @detail_action()
    def test_detail(self, pk, data=None, **kwargs):
        instance = self.get_object_or_404(pk)
        return instance.name, 200

    @list_action(name='named_list')
    def some_other_list(self, data=None, **kwargs):
        return 'some data', 200

    @detail_action(name='named_detail')
    def some_other_detail(self, pk, data=None, **kwargs):
        instance = self.get_object_or_404(pk)
        return instance.name, 200
"""

class ResourceBindingTestCase(ChannelsLiveServerTestCase):

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
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

    @pytest.mark.skip
    def test_list_action(self):
        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
            'action': 'test_list',
            'pk': None,
            'data': {},
            'request_id': 'client-request-id',
        }))

        expected = {
            'action': 'test_list',
            'errors': [],
            'data': 'some data',
            'response_status': 200,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    @pytest.mark.skip
    def test_detail_action(self):
        instance = TestModel.objects.create(name='some-test')

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
            'action': 'test_detail',
            'pk': instance.id,
            'data': {},
            'request_id': 'client-request-id'
        }))

        expected = {
            'action': 'test_detail',
            'errors': [],
            'data': instance.name,
            'response_status': 200,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    @pytest.mark.skip
    def test_named_list_action(self):
        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
            'action': 'named_list',
            'pk': None,
            'data': {},
            'request_id': 'client-request-id',
        }))

        expected = {
            'action': 'named_list',
            'errors': [],
            'data': 'some data',
            'response_status': 200,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    @pytest.mark.skip
    def test_named_detail_action(self):
        instance = TestModel.objects.create(name='some-test')

        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
            'action': 'named_detail',
            'pk': instance.id,
            'data': {},
            'request_id': 'client-request-id'
        }))

        expected = {
            'action': 'named_detail',
            'errors': [],
            'data': instance.name,
            'response_status': 200,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    @pytest.mark.skip
    def test_bad_permission_reply(self):
        mock_has_perm = Mock()
        mock_has_perm.return_value = False
        with patch.object(TestModelResourceBinding, 'has_permission', mock_has_perm):
            json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
                'action': 'named_detail',
                'pk': 546,
                'data': {},
                'request_id': 'client-request-id'
            }))

            expected = {
                'action': 'named_detail',
                'errors': ['Permission Denied'],
                'data': None,
                'response_status': 401,
                'request_id': 'client-request-id'
            }

            self.assertEqual(json_content['payload'], expected)
            self.assertEqual(mock_has_perm.called, True)

    @pytest.mark.skip
    def test_bad_action_reply(self):
        json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel',{
            'action': 'named_detail_not_set',
            'pk': 123,
            'data': {},
            'request_id': 'client-request-id'
        }))

        expected = {
            'action': 'named_detail_not_set',
            'errors': ['Invalid Action'],
            'data': None,
            'response_status': 400,
            'request_id': 'client-request-id'
        }

        self.assertEqual(json_content['payload'], expected)

    @pytest.mark.skip
    def test_is_authenticated_permission(self):

        with patch.object(TestModelResourceBinding, 'permission_classes', (IsAuthenticated,)):
            content = {
                'action': 'test_list',
                'pk': None,
                'data': {},
                'request_id': 'client-request-id',
            }
            json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', content))
            # It should block the request
            self.assertEqual(json_content['payload']['response_status'], 401)

            user = User.objects.create(username="testuser", password="123")
            self.client.force_login(user)
            self.client._session_cookie = True

            json_content = self._send_and_consume('websocket.receive', self._build_message('testmodel', content))

            self.assertEqual(json_content['payload']['response_status'], 200)
