import socket
from urllib.parse import urlparse

def is_private_ip(ip: str) -> bool:
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        first = int(parts[0])
        if first == 10:
            return True
        if first == 172 and 16 <= int(parts[1]) <= 31:
            return True
        if first == 192 and int(parts[1]) == 168:
            return True
        if first == 127:
            return True
        if ip.startswith('169.254.'):
            return True
    except:
        pass
    return False

def resolve_and_validate(url: str) -> bool:
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
