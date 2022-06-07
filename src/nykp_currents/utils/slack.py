from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .secrets import get_slack_token


class NykpSlackChannels:
    test_python_api = 'test-python-api'
    hudson_conditions = 'hudson-conditions'
    hudson_sessions = 'hudson-sessions'


def get_client(token=None):
    if token is None:
        token = get_slack_token()
    return WebClient(token=token)


def post_message(text: str, channel=NykpSlackChannels.test_python_api, client=None, token=None):
    try:
        if client is None:
            client = get_client(token=token)
        return client.chat_postMessage(
            channel=channel,
            text=text,
            unfurl_links=False,
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print(f"SlackApiError: {e.response['error']}")  # something like 'invalid_auth', 'channel_not_found'
        raise
