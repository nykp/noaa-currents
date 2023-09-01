import slack_sdk
from slack_sdk.errors import SlackApiError

from .secrets import get_slack_bot_token, get_slack_user_token


class NykpSlackChannels:
    test_python_api = 'test-python-api'
    hudson_conditions = 'hudson-conditions'
    hudson_sessions = 'hudson-sessions'


def get_client(token=None, user=False):
    if token is None:
        if user:
            token = get_slack_user_token()
        else:
            token = get_slack_bot_token()
    return slack_sdk.WebClient(token=token)


def post_message(text: str, channel=NykpSlackChannels.test_python_api, client=None, token=None, **kwargs):
    try:
        if client is None:
            client = get_client(token=token)
        return client.chat_postMessage(
            channel=channel,
            text=text,
            **kwargs
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print(f"SlackApiError: {e.response['error']}")  # something like 'invalid_auth', 'channel_not_found'
        raise


def post_file(path: str, channel: str, comment=None, client=None, token=None) -> dict:
    if client is None:
        client = get_client(token=token)
    resp = client.files_upload(file=path, channels=channel, initial_comment=comment)
    return resp.data['file']
