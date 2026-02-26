"""
Middleware to force admin password change on first login.

The installer creates a marker file at /opt/cdn-portal/.password_change_required.
On first login, the admin is redirected to the password change page.
The marker is removed after the password is successfully changed.
"""
import os
from django.shortcuts import redirect
from django.urls import reverse

MARKER_FILE = '/opt/cdn-portal/.password_change_required'

EXEMPT_PATHS = (
    '/admin/password_change/',
    '/admin/password_change/done/',
    '/admin/logout/',
    '/admin/login/',
)


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.is_staff
            and os.path.exists(MARKER_FILE)
            and not any(request.path.startswith(p) for p in EXEMPT_PATHS)
        ):
            return redirect(reverse('admin:password_change'))

        response = self.get_response(request)

        # After a successful password change the done view is called — remove marker
        if request.path == reverse('admin:password_change_done') and response.status_code in (200, 302):
            try:
                os.remove(MARKER_FILE)
            except FileNotFoundError:
                pass

        return response
