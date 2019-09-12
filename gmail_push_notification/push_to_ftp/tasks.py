# Create your tasks here
from __future__ import absolute_import, unicode_literals
import logging
from celery import shared_task
from gmail_push_notification.gmail_utils import push_attachments

log = logging.getLogger(__name__)

@shared_task
def process_gmail_attachments(response):
    """Process gmail attachment.
    """
    log.info("process_gmail_attachments: response: [%s]" % response)
    result = push_attachments.run(response)
    log.info("process_gmail_attachments: Processing completed")     

