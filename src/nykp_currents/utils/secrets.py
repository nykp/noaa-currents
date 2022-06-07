import os

SECRETS_DIR = os.path.abspath(os.path.join(__file__, '../../../../.secrets'))
SLACK_TOKEN_FILE = os.path.join(SECRETS_DIR, 'slack_app_token')


def get_slack_token():
    with open(SLACK_TOKEN_FILE) as f:
        return f.readlines()[0]
