from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .secrets import get_slack_token

CHANNEL = 'test-python-api'


def get_client(token=None):
    if token is None:
        token = get_slack_token()
    return WebClient(token=token)


def post_message(text: str, client=None, token=None):
    try:
        if client is None:
            client = get_client(token=token)
        return client.chat_postMessage(
            channel="test-python-api",
            text=text
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print(f"SlackApiError: {e.response['error']}")  # something like 'invalid_auth', 'channel_not_found'
        raise
