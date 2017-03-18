from django.core.serializers.json import json
from channels.generic.websockets import WebsocketDemultiplexer, WebsocketMultiplexer
from channels import Group
from channels.sessions import channel_session
from urllib import parse
from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth.models import User


class Routing(WebsocketDemultiplexer):
    def receive(self, content, **kwargs):
        """Forward messages to all consumers."""
        # Check the frame looks good
        if isinstance(content, dict) and "stream" in content and "payload" in content:
            # Match it to a channel
            for stream, consumer in self.consumers.items():
                if stream == content['stream']:
                    # Extract payload and add in reply_channel
                    payload = content['payload']
                    if not isinstance(payload, dict):
                        raise ValueError("Multiplexed frame payload is not a dict")
                    # The json consumer expects serialized JSON
                    self.message.content['text'] = json.dumps(payload)
                    # Send demultiplexer to the consumer, to be able to answer
                    kwargs['multiplexer'] = WebsocketMultiplexer(stream, self.message.reply_channel)
                    set_channel_session(message=self.message)
                    # Dispatch message
                    consumer(self.message, **kwargs)
                    return

            raise ValueError("Invalid multiplexed frame received (stream not mapped)")
        else:
            raise ValueError("Invalid multiplexed **frame received (no channel/payload key)")

    def connect(self, message, **kwargs):
        set_channel_session(message=self.message)

        username, password = get_username_and_password(message)
        user = authenticate(username=username, password=password)
        if user:
            message.channel_session['_auth_user_id'] = user.pk
            message.channel_session['_auth_user_hash'] = user.get_session_auth_hash()
            message.channel_session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'

        self.message.reply_channel.send({"accept": True})
        for stream, consumer in self.consumers.items():
            kwargs['multiplexer'] = WebsocketMultiplexer(stream, self.message.reply_channel)
            consumer(message, **kwargs)


@channel_session
def set_channel_session(message):
    pass


def get_username_and_password(message):
    username = message.content.get('username', None)
    password = message.content.get('password', None)
    if username is None:
        if 'query_string' in message:
            query = parse.parse_qs(message['query_string'])
            if 'username' not in query:
                return None, None
            username = query['username'][0]
            password = query['password'][0]
    return username, password
