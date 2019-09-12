#!/usr/bin/env python
import sys
import logging
import logging.handlers
from oauth2client import client
from oauth2client.client import flow_from_clientsecrets

LOG_FILENAME = "/opt/logs/refresh_token.log"
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*1024*1024, backupCount=30)
#handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

CLIENT_SECRETS_FILE = '/home/akshay/work/fa/gmail_push_notifications/client_secret_enact.json'
REDIRECT_URI = 'http://localhost:8090'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    # Add other requested scopes.
]

#SCOPE = u'https://www.googleapis.com/auth/gmail.readonly'

#logging.basicConfig(format='%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p : ',
#                    filename='GoogleAuthentication.log', level=logging.DEBUG)


def main():
    """Retrieve the access and refresh token.
    """
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SCOPES, redirect_uri='https://localhost:8080')
    authorize_url = flow.step1_get_authorize_url()
    log.info("URL to get the verification code [%s]" % authorize_url)
    print("Hit this URL to get the code: \n%s\n" % authorize_url)
    code = raw_input("Enter the Code: ").strip()
    log.info("Verification code: [%s]" % code)
    try:
        credential = flow.step2_exchange(code)
    except client.FlowExchangeError, ex:
        print("Authentication failed: FlowExchangeError: [%s]" % str(ex))
        log.error("Authentication failed: FlowExchangeError: [%s]" % str(e))
        sys.exit(1)
    print "OAuth2 authorization successful!"
    print "AccessToken: [%s], RefreshToekn: [%s]" % (credential.access_token, credential.refresh_token)
    log.info("OAuth2 authorization successful!")
    log.info("AccessToken: [%s], RefreshToekn: [%s]" % (credential.access_token, credential.refresh_token))

if __name__ == '__main__':
    main()
