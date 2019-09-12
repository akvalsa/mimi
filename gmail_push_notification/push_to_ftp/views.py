import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from push_to_ftp import tasks

log = logging.getLogger(__name__)

@csrf_exempt
def process_gmail(request):
    """View to process gmail messages.
    """
    try:
        request_data = request.body
        log.info("process_gmail: Request Body: [%s]" % request_data)
        # Prepare json data 
        jdata = json.loads(request_data)
        log.info("process_gmail: Request Json: [%s]" % jdata)
        # Send the data for processing to celery tasks
        tasks.process_gmail_attachments.delay(jdata)
        return JsonResponse(jdata)
    except Exception as ex:
        log.info("process_gmail: Exception: [%s]" % str(ex))
        return JsonResponse({})
