import logging
from html import escape as escape_xml_text

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.auth import AuthContext, get_auth_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dav", tags=["dav"])


def _dav_path_owner_user_id(path: str) -> str | None:
    normalized_path = path.strip("/")
    if not normalized_path:
        return None
    owner_user_id, _, _ = normalized_path.partition("/")
    return owner_user_id or None


def _ensure_dav_owner_scope(path: str, auth_context: AuthContext) -> None:
    owner_user_id = _dav_path_owner_user_id(path)
    if owner_user_id is None:
        raise HTTPException(
            status_code=403,
            detail="DAV path must include an owner user",
        )
    if owner_user_id == auth_context.user_id:
        return
    raise HTTPException(
        status_code=403,
        detail="DAV path belongs to a different user",
    )


@router.api_route(
    "/{path:path}",
    methods=["PROPFIND", "REPORT", "MKCOL", "GET", "PUT", "DELETE", "OPTIONS"],
)
async def dav_handler(
    request: Request,
    path: str,
    auth_context: AuthContext = Depends(get_auth_context),
):
    """
    Skeleton endpoint for CalDAV / WebDAV routing.
    In the future, this will parse XML namespaces and bridge
    Naruon's Tasks and Events into DAV compliant responses.
    """
    _ensure_dav_owner_scope(path, auth_context)
    safe_path = repr(path)[1:-1]
    logger.info("DAV Request: %s /%s", request.method, safe_path)

    if request.method == "OPTIONS":
        headers = {
            "DAV": "1, 2, 3, calendar-access, addressbook",
            "Allow": (
                "OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, COPY, MOVE, MKCOL, "
                "PROPFIND, PROPPATCH, LOCK, UNLOCK, REPORT"
            ),
        }
        return Response(status_code=200, headers=headers)

    if request.method == "PROPFIND":
        # Simulate virtual collections: /dav/projects/
        is_collection = path.endswith("/") or path == "" or "projects" in path
        resourcetype = "<D:collection/>" if is_collection else ""
        escaped_href = escape_xml_text(f"/api/dav/{path}")
        escaped_display_name = escape_xml_text(path.split("/")[-1] or "Root")

        xml_response = f"""<?xml version="1.0" encoding="utf-8" ?>
<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:response>
    <D:href>{escaped_href}</D:href>
    <D:propstat>
      <D:prop>
        <D:resourcetype>{resourcetype}</D:resourcetype>
        <D:displayname>{escaped_display_name}</D:displayname>
      </D:prop>
      <D:status>HTTP/1.1 200 OK</D:status>
    </D:propstat>
  </D:response>
</D:multistatus>"""
        return Response(
            content=xml_response, media_type="application/xml", status_code=207
        )

    if request.method == "PUT":
        body = await request.body()
        safe_path = repr(path)[1:-1]
        logger.info("DAV PUT received %s bytes at /%s", len(body), safe_path)
        return Response(
            content=(
                "Provider-backed DAV writeback is not implemented; use signed "
                "writeback-intent APIs until source, capability, and "
                "ETag/If-Match checks are enforced."
            ),
            media_type="text/plain",
            status_code=501,
        )

    return Response(content="Not Implemented", status_code=501)
