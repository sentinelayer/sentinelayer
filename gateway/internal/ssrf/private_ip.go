package ssrf

import (
    "net"
    "strings"
)

// Deny private, non-routable, documentation, benchmarking, carrier-grade NAT,
// and special-purpose addresses. Parsing an IP alone is not proof of public
// reachability; public DNS resolution also needs egress enforcement.
var blockedIPBlocks []*net.IPNet

func init() {
    for _, cidr := range []string{
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.0.0.0/24",
        "192.0.2.0/24",
        "192.88.99.0/24",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "198.51.100.0/24",
        "203.0.113.0/24",
        "224.0.0.0/4",
        "240.0.0.0/4",
        "::/128",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
        "2001:db8::/32",
        "ff00::/8",
    } {
        _, block, err := net.ParseCIDR(cidr)
        if err != nil {
            panic("invalid bundled network block: " + cidr)
        }
        blockedIPBlocks = append(blockedIPBlocks, block)
    }
}

func hostWithoutPort(raw string) string {
    host := strings.TrimSpace(raw)
    if strings.HasPrefix(host, "[") {
        if parsed, port, err := net.SplitHostPort(host); err == nil && port != "" {
            return parsed
        }
        if strings.HasSuffix(host, "]") {
            return strings.TrimSuffix(strings.TrimPrefix(host, "["), "]")
        }
    }
    if parsed, port, err := net.SplitHostPort(host); err == nil && port != "" {
        return parsed
    }
    // URL request Host can contain a single colon followed by a port.
    if strings.Count(host, ":") == 1 {
        if parsed, port, err := net.SplitHostPort(host); err == nil && port != "" {
            return parsed
        }
    }
    return host
}

func IsPrivateIP(ipStr string) bool {
    ip := net.ParseIP(hostWithoutPort(ipStr))
    if ip == nil {
        return false
    }
    for _, block := range blockedIPBlocks {
        if block.Contains(ip) {
            return true
        }
    }
    return false
}

func IsBlockedHost(raw string) bool {
    host := strings.ToLower(strings.TrimSuffix(hostWithoutPort(raw), "."))
    if host == "" {
        return true
    }
    if IsPrivateIP(host) {
        return true
    }
    for _, base := range []string{"localhost", "localhost.localdomain", "metadata.google.internal"} {
        if host == base || strings.HasSuffix(host, "."+base) {
            return true
        }
    }
    return strings.HasSuffix(host, ".local")
}
