from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
import json

META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")

@csrf_exempt
def meta_lead_webhook(request):

    # 🔹 Verificación obligatoria de Meta
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == META_VERIFY_TOKEN:
            return HttpResponse(challenge)

        return HttpResponse("Invalid verify token", status=403)

    # 🔹 POST real (luego lo usamos)
    if request.method == "POST":
        return JsonResponse({"status": "ok"})

    return HttpResponse(status=405)
