package ssrf

import "testing"

func TestRejectsNonGlobalNumericDestinations(t *testing.T) {
    cases := []string{
        "127.0.0.1", "10.1.2.3", "100.64.0.1", "100.127.255.254",
        "169.254.169.254", "172.16.0.1", "192.168.1.3",
        "192.0.2.10", "198.18.0.1", "198.51.100.1",
        "203.0.113.4", "224.1.1.1", "255.255.255.255",
        "::", "::1", "fe80::1", "fc00::1", "2001:db8::1",
        "ff02::1", "::ffff:127.0.0.1",
        "[::1]:443", "127.0.0.1:8443",
    }
    for _, addr := range cases {
        if !IsPrivateIP(addr) {
            t.Errorf("non-global IP must be blocked: %s", addr)
        }
    }
}

func TestPermitsPublicIPAndHostnameWithoutFalsePositives(t *testing.T) {
    for _, host := range []string{
        "8.8.8.8", "1.1.1.1", "2606:4700:4700::1111",
        "example.com", "notlocalhost.example", "metadata.google.internal.evil.example",
    } {
        if IsPrivateIP(host) {
            t.Errorf("public IP or domain incorrectly considered private: %s", host)
        }
        if IsBlockedHost(host) {
            t.Errorf("public IP or domain incorrectly blocked: %s", host)
        }
    }
}

func TestLocalHostsMustMatchCompleteDNSLabels(t *testing.T) {
    for _, host := range []string{
        "localhost", "localhost.", "LOCALHOST:8080",
        "foo.localhost", "localhost.localdomain",
        "metadata.google.internal", "METADATA.GOOGLE.INTERNAL.:443",
        "api.service.local", "[::1]:443", "169.254.169.254:80",
    } {
        if !IsBlockedHost(host) {
            t.Errorf("local or metadata host must be blocked: %s", host)
        }
    }
}
