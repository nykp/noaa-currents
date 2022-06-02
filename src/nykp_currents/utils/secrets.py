SLACK_TOKEN_FILE_PATH = 'secrets/slack_app_token'


def get_slack_token():
    with open(SLACK_TOKEN_FILE_PATH) as f:
        return f.readlines()[0]
