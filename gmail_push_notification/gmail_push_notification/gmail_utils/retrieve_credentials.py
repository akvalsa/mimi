#!/usr/bin/env python
"""
    Script for retrieving google authentication object from refresh token.
"""

import json
import requests
import logging
import logging.handlers
import httplib2
from apiclient import discovery
from oauth2client.client import AccessTokenCredentials, AccessTokenCredentialsError
from gmail_push_notification.gmail_utils import config

LOG_DIR = config.LOG_DIR
LOG_FILENAME = "%s/retrieve_credentials.log" % LOG_DIR
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=30)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

CLIENT_SECRETS_FILE = config.CLIENT_SECRETS_FILE
REFRESH_TOKEN = config.REFRESH_TOKEN
GOOGLE_API = config.GOOGLE_API

def get_access_token(refresh_token):
    """Retrieve access token from refresh token. 
    """
    try:
        # Get the client information
        result = _get_client_info()
        status, message, client_info = result
        log.info("get_access_token: _get_client_info, result: [%s]" % (result,))
        if status != 0:
            log.info("get_access_token: Unbale to get client info.")
            raise Exception(message)
        # Build the data for google api
        client_id, client_secret = client_info
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        log.info("get_access_token: data: [%s]" % data)
        # Call the google api
        headers = {u'content-type': u'application/x-www-form-urlencoded'}
        cred = requests.post(url=GOOGLE_API, data=data, headers=headers)
        # Fetch the access token
        access_token = cred.content.split(',')[0].split(':')[1]
        log.info("get_access_token: access_token: [%s]" % access_token)
        if access_token is not None:
            return access_token
        else:
            log.info("get_access_token: Unable to get access token.")
            return None
    except Exception as ex:
        log.info("get_access_token: Exception: [%s]" % str(ex))


def _get_credentials(access_token):
    """Retrieve credentials object from access token.
    """
    try:
        credentials = AccessTokenCredentials(access_token=access_token, user_agent='user-agent')
        if credentials.invalid or credentials.access_token_expired:
            log.error("_get_credentials: Access token expired/invalid.")
            return None
        log.info("_get_credentials: credentials: [%s]" % credentials)
        return credentials
    except AccessTokenCredentialsError as ex:
        log.error("_get_credentials: Exception: [%s]" % str(ex))


def _get_client_info():
    """
    """
    try:
        status, message = 0, ''
        _client_data = open(CLIENT_SECRETS_FILE)
        log.info("_get_client_info: _client_data: [%s]" % _client_data)
        client_data = json.load(_client_data)
        client_id = client_data["installed"]["client_id"]
        client_secret = client_data["installed"]["client_secret"]
        info = (client_id, client_secret)
        log.info("_get_client_info: info: [%s]" % (info, ))
        return (status, message, info)
    except Exception as ex:
        log.info("_get_client_info: Exception: [%s]" % str(ex))
        status, message = -1, "Excption in getting client information."
        return (status, message, {})


def get_credentials():
    """Returns Service object. 
    """
    # Get the access token from refresh token.
    access_token = get_access_token(REFRESH_TOKEN)
    log.info("get_credentials: access_token: [%s]" % access_token)
    if access_token:
        access_token = access_token[2:-1]
        # Get credentials object
        credentials = _get_credentials(access_token)
        log.info("get_credentials: credentials: [%s]" % credentials)
        return credentials
    else:
        log.info("get_credentials: Unable to get credentials.")

if __name__ == '__main__':
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    # Get Current historyID
    req = service.users().getProfile(userId='me').execute()
    res = req.get('historyId')
    print res
