"""One consistent JSON error format for the whole API: {"error": "...", "details": ...}."""
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # Django returns a generic 500 and logs it - no details leaked.

    data = response.data
    if isinstance(data, dict) and set(data.keys()) == {"detail"}:
        payload = {"error": str(data["detail"])}
    else:
        payload = {"error": "Invalid request.", "details": data}
    return Response(payload, status=response.status_code, headers=dict(response.headers))
