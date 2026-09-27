from django.http import JsonResponse


def panel(_request):
    return JsonResponse({"service": "panel-api", "status": "ready"})
