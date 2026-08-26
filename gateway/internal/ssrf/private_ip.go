package ssrf

import (
    "net"
    "strings"
)

var privateIPBlocks []*net.IPNet

func init() {
    for _, cidr := range []string{
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "0.0.0.0/8",
        "224.0.0.0/4",
        "240.0.0.0/4",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    } {
        _, block, _ := net.ParseCIDR(cidr)
        privateIPBlocks = append(privateIPBlocks, block)
    }
}

func IsPrivateIP(ipStr string) bool {
    ip := net.ParseIP(ipStr)
    if ip == nil {
        return false
    }
    for _, block := range privateIPBlocks {
        if block.Contains(ip) {
            return true
        }
    }
    return false
}

func IsBlockedHost(host string) bool {
    blocked := []string{
        "localhost",
        "metadata.google.internal",
        "169.254.169.254",
    }
    for _, b := range blocked {
        if strings.Contains(strings.ToLower(host), b) {
            return true
        }
    }
    return false
}
