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

    # 🔹 POST real de Meta
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "invalid json"}, status=400)

        print("META WEBHOOK PAYLOAD:", payload)

        # 🔹 Extraer leadgen_id (forma estándar)
        leadgen_id = None

        entry = payload.get("entry", [])
        if entry:
            changes = entry[0].get("changes", [])
            if changes:
                leadgen_id = changes[0].get("value", {}).get("leadgen_id")

        print("LEADGEN ID:", leadgen_id)

        return JsonResponse({"status": "ok"})

    return HttpResponse(status=405)
