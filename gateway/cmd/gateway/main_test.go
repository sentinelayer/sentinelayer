package main

import (
	"net/http/httptest"
	"os"
	"testing"
)

func TestListenAddressUsesPlatformPort(t *testing.T) {
	previous := os.Getenv("PORT")
	t.Cleanup(func() { _ = os.Setenv("PORT", previous) })

	for _, test := range []struct {
		name string
		port string
		want string
	}{
		{name: "default", port: "", want: ":8080"},
		{name: "railway port", port: "49152", want: ":49152"},
	} {
		t.Run(test.name, func(t *testing.T) {
			if err := os.Setenv("PORT", test.port); err != nil {
				t.Fatal(err)
			}
			got, err := listenAddress()
			if err != nil || got != test.want {
				t.Fatalf("listenAddress() = %q, %v; want %q", got, err, test.want)
			}
		})
	}
}

func TestListenAddressRejectsInvalidPort(t *testing.T) {
	previous := os.Getenv("PORT")
	t.Cleanup(func() { _ = os.Setenv("PORT", previous) })
	for _, port := range []string{"0", "65536", "not-a-port"} {
		if err := os.Setenv("PORT", port); err != nil {
			t.Fatal(err)
		}
		if _, err := listenAddress(); err == nil {
			t.Fatalf("listenAddress() accepted invalid port %q", port)
		}
	}
}

func TestClientAddressStripsEphemeralPort(t *testing.T) {
	req := httptest.NewRequest("GET", "http://gateway.test/", nil)
	req.RemoteAddr = "203.0.113.7:54321"
	if got := clientAddress(req); got != "203.0.113.7" {
		t.Fatalf("clientAddress() = %q; want stable host", got)
	}
}

func TestClassifyEndpointAuthBootstrapRoutes(t *testing.T) {
	for _, test := range []struct {
		path string
		want string
	}{
		{path: "/api/v1/auth/login", want: "public"},
		{path: "/api/v1/auth/register", want: "public"},
		{path: "/api/v1/auth/logout", want: "critical"},
		{path: "/api/v1/auth/change-password", want: "critical"},
		{path: "/api/v1/auth/login/extra", want: "critical"},
		{path: "/api/v1/admin/users", want: "critical"},
	} {
		t.Run(test.path, func(t *testing.T) {
			req := httptest.NewRequest("POST", "http://gateway.test"+test.path, nil)
			if got := classifyEndpoint(req); got != test.want {
				t.Fatalf("classifyEndpoint(%q) = %q; want %q", test.path, got, test.want)
			}
		})
	}
}
