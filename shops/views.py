from django.db import connection
from django.http import JsonResponse


def panel(_request):
    return JsonResponse({"service": "panel-api", "status": "ready", "shops": []})


def live(_request):
    return JsonResponse({"status": "live"})


def ready(_request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ready"})
