import hashlib
import re
from urllib.parse import urlsplit, urlunsplit
 
 
def normalize_url(url):
    """Remove tracking parameters and URL fragments."""
    if not url:
        return None
 
    parts = urlsplit(url.strip())
 
    clean_url = urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        parts.path.rstrip("/"),
        "",
        ""
    ))
 
    return clean_url
 
 
def generate_article_id(guid=None, url=None):
    """
    Prefer RSS GUID.
    If GUID is unavailable, generate ID from canonical URL.
    """
    identity = guid or normalize_url(url)
 
    if not identity:
        raise ValueError("Article must contain a GUID or URL")
 
    identity = re.sub(r"\s+", " ", identity.strip())
 
    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()