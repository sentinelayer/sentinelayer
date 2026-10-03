package waf

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
)

// Fixed developer-authored regression corpus, not customer calibration data.
// Report every case individually so benign blocks cannot disappear in a rate.
func TestLabelledRegressionCorpus(t *testing.T) {
	engine, err := NewEngine("../../../waf/rules")
	if err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		name, value string
		attack      bool
	}{
		{"search", "cloud security indonesia", false},
		{"apostrophe", "O'Reilly", false},
		{"unicode", "Jakarta café 日本語", false},
		{"email", "ivan@example.test", false},
		{"math", "1 + 1 = 2", false},
		{"url", "https://example.test/docs?q=hello", false},
		{"json-text", `{"title":"Quarterly report","count":42}`, false},
		{"markdown", "# Hello\n**World**", false},
		{"comparison", "price < 100 and stock > 0", false},
		{"uuid", "6f01d176-58df-4e6a-bbd0-5be014259cee", false},
		{"sql-tautology", "' OR 1=1 -- ", true},
		{"sql-union", "' UNION SELECT password FROM users -- ", true},
		{"sql-drop", "'; DROP TABLE users; -- ", true},
		{"sql-time", "1' AND SLEEP(5) -- ", true},
		{"xss-script", "<script>alert(1)</script>", true},
		{"xss-event", "<img src=x onerror=alert(1)>", true},
		{"xss-svg", "<svg onload=alert(1)>", true},
		{"xss-protocol", "javascript:alert(1)", true},
		{"command", "; cat /etc/passwd", true},
		{"traversal-argument", "../../etc/passwd", true},
	}
	blockedAttack, blockedBenign, attacks, benign := 0, 0, 0, 0
	for _, item := range cases {
		t.Run(item.name, func(t *testing.T) {
			request := httptest.NewRequest(http.MethodGet, "http://example.test/search?q="+url.QueryEscape(item.value), nil)
			request.Header.Set("User-Agent", "SentinelLayer-Corpus/1.0")
			request.Header.Set("Accept", "application/json")
			blocked, rule, message := engine.ProcessRequest(request)
			if item.attack {
				attacks++
				if blocked {
					blockedAttack++
				}
			} else {
				benign++
				if blocked {
					blockedBenign++
				}
			}
			t.Logf("attack=%v blocked=%v rule=%d message=%s", item.attack, blocked, rule, message)
			if blocked != item.attack {
				t.Errorf("classification mismatch")
			}
		})
	}
	t.Logf("synthetic corpus: attack blocks %d/%d; benign blocks %d/%d; no production detection/FP claim", blockedAttack, attacks, blockedBenign, benign)
}
