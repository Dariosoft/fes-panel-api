from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from identity.navigation import build_google_login_redirect_url


class GoogleLoginRedirectView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, _request: Request) -> HttpResponseRedirect:
        location = build_google_login_redirect_url(
            settings.ACCOUNTS_PUBLIC_BASE_URL,
            settings.PANEL_PUBLIC_ORIGIN,
        )
        return HttpResponseRedirect(location)
