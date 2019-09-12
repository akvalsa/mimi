import json
import logging
import logging.handlers
import re
import base64
import httplib2

from apiclient import discovery

from gmail_credentials import get_credentials

LOG_FILENAME = "/opt/logs/push_attachments.log"
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*1024*1024, backupCount=30)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)

SOURCE_EMAIL = '<email>'
STORE_DIR = '/opt/data/'

def run(response):
    """Celery to push the attachments to the FTP server.
    """
    log.info("response: [%s]" % response)
    try:
        user_id = 'me'
        # Get the message data from response
        _data = response.get('message', {}).get('data')
        if not _data:
            log.info("Message data not available in response.")
            return
        # Decrypt data
        data = base64.b64decode(_data)        
        data = json.loads(data)
        log.info("Message data: [%s]" % data)
        email = data['emailAddress']
        history_id = data['historyId']
        if email != SOURCE_EMAIL:
            log.info("Received email from different source.")
            return
        # Build google service object from credentials
        credentials = get_credentials()        
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
        log.info("Google service: [%s]" % service)
        # Get the history of messages
        status, info, messages = listHistory(service, user_id, history_id)
        log.info("listHistory status: [%s], info: [%s], message count: [%s]" % (status, info, len(messages)))
        if not status:
            log.info("Unable to get the user messages.")
            return
        # Get unique message ids
        msg_ids = set()
        for message in messages:
            _messages = message.get('messages', [])
            for _message in _messages:
                if _message.get('id'):
                    msg_ids.add(_message['id'])
        # Process the messages
        status, info = processMessages(service, user_id, msg_ids)    
        log.info("processMessages: status: [%s], info: [%s]" % (status, info))
    except Exception as ex:
        log.info("Exception in run, Exception: [%s]" % str(ex))
        raise ex

def processMessages(service, user_id, msg_ids):
    """Processes the messages
    """
    try:
        status, info = True, ''
        # Build the regular expression to extract email
        pat = re.compile('<(.*?)>')
        log.info("Processing [%s] messages" % len(msg_ids))
        for msg_id in msg_ids:
            log.info("Processing messageID: [%s]" % msg_id)        
            message = service.users().messages().get(userId=user_id, id=msg_id).execute()
            # Check if email has attachment
            parts = message.get('payload', {}).get('parts')
            if not parts:
                log.info("Attachment not present.")
                continue
            # Check if the email is from source email id.
            headers = message.get('payload', {}).get('headers', [])
            for header in headers:
                if header['name'] == 'From':
                    _email = header['value']
                    emails = pat.findall(_email)
                    email = emails[0] if emails else ''
                    log.info("Got email from: [%s]" % email)
                    if email == SOURCE_EMAIL:
                        log.info("Email matches")
                        status, info = downloadAttachment(service, user_id, msg_id, parts)
                        log.info("downloadAttachment: status: [%s], info: [%s]" % (status, info))
                        if not status:
                            raise ValueError(info)
        return (status, info)
    except ValueError as ex:
        log.info("processMessages, ValueError: [%s]" % str(ex))
        return (False, str(ex))
    except Exception as ex:
        log.info("processMessages, Exception: [%s]" % str(ex))
        return (False, str(ex))

def downloadAttachment(service, user_id, msg_id, message_parts):
    """Download the attachment.
    """
    log.info("In downloadAttachment: user_id: [%s], msg_id: [%s]" % (user_id, msg_id))
    status, info = True, ''
    try:
        for part in message_parts:
          if part['filename']:
            log.info("In downloadAttachment: filename: [%s]" % part['filename'])
            if 'data' in part['body']:
                data=part['body']['data']
            else:
                att_id=part['body']['attachmentId']
                att=service.users().messages().attachments().get(userId=user_id, messageId=msg_id,id=att_id).execute()
                data=att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            filename = part['filename']
            log.info("downloadAttachment: filename: [%s]" % filename)
            path = ''.join([STORE_DIR, filename])
            f = open(path, 'w')
            f.write(file_data)
            f.close()
        return (status, info)
    except Exception as ex:
        log.info("Unable to download attachment, Exception: [%s]" % str(ex))        
        return (False, 'downloadAttachment: Exception: [%s]' % (str(ex)))


def listHistory(service, user_id, start_history_id=None):
  """List History of all changes to the user's mailbox.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    start_history_id: Only return Histories at or after start_history_id.

  Returns:
    A list of mailbox changes that occurred after the start_history_id.
  """
  try:
    history = (service.users().history().list(userId=user_id,
                                              startHistoryId=start_history_id)
               .execute())
    changes = history['history'] if 'history' in history else []
    while 'nextPageToken' in history:
      page_token = history['nextPageToken']
      history = (service.users().history().list(userId=user_id,
                                        startHistoryId=start_history_id,
                                        pageToken=page_token).execute())
      changes.extend(history['history'])

    return (True, '', changes)
  except errors.HttpError, error:
    message = 'ListHistory Exception: [%s]' % error
    log.info(message)
    return (False, message, [])

if __name__ == "__main__":
    response = {'message': {}, 'subscription': 'projects/myproject/subscriptions/mysubscription'}
    response['message']['data'] = 'eyJlbWFpbEFkZHJlc3MiOiAiYWtzaGF5LnZhbHNhQGZvcmdlYWhlYWQuaW8iLCAiaGlzdG9yeUlkIjogIjEyMTAzIn0='
    response['message']['message_id'] = '1234567890'
    run(response)
