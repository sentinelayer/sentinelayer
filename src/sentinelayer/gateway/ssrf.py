import socket
import ipaddress
from urllib.parse import urlparse

BLOCKED_IPS = [
    "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "169.254.0.0/16", "::1", "fc00::/7", "fe80::/10"
]

def is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for network in BLOCKED_IPS:
            if ip_obj in ipaddress.ip_network(network, strict=False):
                return True
        return False
    except:
        return True

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
