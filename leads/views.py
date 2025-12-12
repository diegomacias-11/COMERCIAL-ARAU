from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import os

META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")

@csrf_exempt
def meta_lead_webhook(request):

    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == META_VERIFY_TOKEN:
            response = HttpResponse(challenge)
            response["Content-Type"] = "text/plain"
            return response

        return HttpResponse("Invalid token", status=403)

    if request.method == "POST":
        return HttpResponse("OK", status=200)

    return HttpResponse(status=405)