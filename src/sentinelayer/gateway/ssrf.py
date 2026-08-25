import socket
from urllib.parse import urlparse

PRIVATE_IPS = [
    '127.0.0.1', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
    '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
    '192.168.', '169.254.'
]

def is_private_ip(ip: str) -> bool:
    for prefix in PRIVATE_IPS:
        if ip.startswith(prefix):
            return True
    return False

def validate_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        ips = socket.gethostbyname_ex(hostname)[2]
        for ip in ips:
            if is_private_ip(ip):
                return False
        return True
    except:
        return False
