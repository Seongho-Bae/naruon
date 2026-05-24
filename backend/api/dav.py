from fastapi import APIRouter, Request, Response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dav", tags=["dav"])

@router.api_route("/{path:path}", methods=["PROPFIND", "REPORT", "MKCOL", "GET", "PUT", "DELETE", "OPTIONS"])
async def dav_handler(request: Request, path: str):
    """
    Skeleton endpoint for CalDAV / WebDAV routing.
    In the future, this will parse XML namespaces and bridge
    Naruon's Tasks and Events into DAV compliant responses.
    """
    safe_path = path.replace("\n", "").replace("\r", "")
    logger.info(f"DAV Request: {request.method} /{safe_path}")
    
    if request.method == "OPTIONS":
        headers = {
            "DAV": "1, 2, 3, calendar-access, addressbook",
            "Allow": "OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK, REPORT"
        }
        return Response(status_code=200, headers=headers)

    if request.method == "PROPFIND":
        # Simulate virtual collections: /dav/projects/
        is_collection = path.endswith("/") or path == "" or "projects" in path
        resourcetype = "<D:collection/>" if is_collection else ""
        
        xml_response = f"""<?xml version="1.0" encoding="utf-8" ?>
<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:response>
    <D:href>/api/dav/{path}</D:href>
    <D:propstat>
      <D:prop>
        <D:resourcetype>{resourcetype}</D:resourcetype>
        <D:displayname>{path.split("/")[-1] or "Root"}</D:displayname>
      </D:prop>
      <D:status>HTTP/1.1 200 OK</D:status>
    </D:propstat>
  </D:response>
</D:multistatus>"""
        return Response(content=xml_response, media_type="application/xml", status_code=207)

    if request.method == "PUT":
        body = await request.body()
        safe_path = path.replace("\n", "").replace("\r", "")
        logger.info(f"DAV PUT received {len(body)} bytes at /{safe_path}")
        return Response(status_code=201) # Created

    return Response(content="Not Implemented", status_code=501)
