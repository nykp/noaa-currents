import os

SECRETS_DIR = os.path.abspath(os.path.join(__file__, '../../../../.secrets'))
SLACK_BOT_TOKEN_FILE = os.path.join(SECRETS_DIR, 'slack_app_bot_token')
SLACK_USER_TOKEN_FILE = os.path.join(SECRETS_DIR, 'slack_app_user_token')


def get_slack_bot_token():
    with open(SLACK_BOT_TOKEN_FILE) as f:
        return f.readlines()[0].strip()


def get_slack_user_token():
    with open(SLACK_USER_TOKEN_FILE) as f:
        return f.readlines()[0].strip()
