from fastapi import Request
from urllib.parse import unquote
import logging
print(".." in unquote("user123/..%2Fother-user/projects/").split("/"))
