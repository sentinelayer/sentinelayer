// Offline labelled WAF evaluation. Never sends requests to a network destination.
package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"strings"

	"github.com/sentinelayer/gateway/internal/waf"
)

type sample struct {
	ID      string            `json:"id"`
	Label   string            `json:"label"`
	Method  string            `json:"method"`
	Path    string            `json:"path"`
	Body    string            `json:"body"`
	Headers map[string]string `json:"headers"`
}
type outcome struct {
	ID      string `json:"id"`
	Label   string `json:"label"`
	Blocked bool   `json:"blocked"`
	Rule    int    `json:"rule_id"`
}
type rate struct {
	Events   int         `json:"events"`
	Total    int         `json:"total"`
	Estimate *float64    `json:"estimate"`
	Interval *[2]float64 `json:"wilson_95_interval"`
}

func measure(events, total int) rate {
	r := rate{Events: events, Total: total}
	if total == 0 {
		return r
	}
	n, p, z := float64(total), float64(events)/float64(total), 1.959963984540054
	d := 1 + z*z/n
	center := (p + z*z/(2*n)) / d
	half := z * math.Sqrt(p*(1-p)/n+z*z/(4*n*n)) / d
	bounds := [2]float64{math.Max(0, center-half), math.Min(1, center+half)}
	r.Estimate = &p
	r.Interval = &bounds
	return r
}
func evaluate(reader io.Reader, engine *waf.Engine) ([]outcome, rate, rate, error) {
	scanner := bufio.NewScanner(io.LimitReader(reader, 10*1024*1024+1))
	scanner.Buffer(make([]byte, 4096), 256*1024)
	seen := map[string]bool{}
	results := []outcome{}
	attack, benign, tp, fp, bytes := 0, 0, 0, 0, 0
	for scanner.Scan() {
		bytes += len(scanner.Bytes()) + 1
		if bytes > 10*1024*1024 || len(results) >= 10000 {
			return nil, rate{}, rate{}, fmt.Errorf("corpus exceeds evaluation budget")
		}
		var s sample
		decoder := json.NewDecoder(strings.NewReader(scanner.Text()))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&s); err != nil {
			return nil, rate{}, rate{}, fmt.Errorf("invalid case at line %d", len(results)+1)
		}
		var trailing any
		if decoder.Decode(&trailing) != io.EOF {
			return nil, rate{}, rate{}, fmt.Errorf("trailing data at line %d", len(results)+1)
		}
		if s.ID == "" || len(s.ID) > 128 || seen[s.ID] || (s.Label != "attack" && s.Label != "benign") {
			return nil, rate{}, rate{}, fmt.Errorf("invalid identity or label at line %d", len(results)+1)
		}
		seen[s.ID] = true
		if s.Method == "" {
			s.Method = http.MethodGet
		}
		if s.Path == "" {
			s.Path = "/"
		}
		parsed, err := url.ParseRequestURI(s.Path)
		if err != nil || !strings.HasPrefix(s.Path, "/") || strings.HasPrefix(s.Path, "//") || parsed.IsAbs() || parsed.Host != "" || len(s.Headers) > 32 {
			return nil, rate{}, rate{}, fmt.Errorf("invalid relative request at line %d", len(results)+1)
		}
		request, err := http.NewRequest(s.Method, "http://corpus.example.test"+s.Path, strings.NewReader(s.Body))
		if err != nil {
			return nil, rate{}, rate{}, fmt.Errorf("invalid method at line %d", len(results)+1)
		}
		request.Header.Set("User-Agent", "SentinelLayer-Offline-Corpus/1.0")
		request.Header.Set("Accept", "application/json")
		for k, v := range s.Headers {
			if len(k) > 128 || len(v) > 8192 || strings.ContainsAny(k+v, "\r\n") {
				return nil, rate{}, rate{}, fmt.Errorf("invalid header at line %d", len(results)+1)
			}
			request.Header.Set(k, v)
		}
		request.RequestURI = s.Path
		blocked, rule, _ := engine.ProcessRequest(request)
		results = append(results, outcome{s.ID, s.Label, blocked, rule})
		if s.Label == "attack" {
			attack++
			if blocked {
				tp++
			}
		} else {
			benign++
			if blocked {
				fp++
			}
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, rate{}, rate{}, fmt.Errorf("corpus cannot be read within per-case budget")
	}
	if len(results) == 0 {
		return nil, rate{}, rate{}, fmt.Errorf("empty corpus")
	}
	return results, measure(tp, attack), measure(fp, benign), nil
}
func run() error {
	corpus := flag.String("corpus", "", "labelled JSONL corpus, max10MiB and10,000 cases")
	rules := flag.String("rules", "../waf/rules", "CRS rules directory")
	provenance := flag.String("provenance", "synthetic", "synthetic or held-out; does not attest representativeness")
	flag.Parse()
	if *corpus == "" || (*provenance != "synthetic" && *provenance != "held-out") {
		return fmt.Errorf("corpus and valid provenance required")
	}
	input, err := os.Open(*corpus)
	if err != nil {
		return fmt.Errorf("cannot open corpus")
	}
	defer input.Close()
	engine, err := waf.NewEngine(*rules)
	if err != nil {
		return err
	}
	hash := sha256.New()
	results, detection, falsePositive, err := evaluate(io.TeeReader(input, hash), engine)
	if err != nil {
		return err
	}
	evidence := struct {
		Provenance    string    `json:"provenance"`
		Digest        string    `json:"corpus_sha256"`
		Detection     rate      `json:"attack_block_rate"`
		FalsePositive rate      `json:"benign_block_rate"`
		Results       []outcome `json:"cases"`
		Acceptance    string    `json:"production_acceptance"`
		Scope         string    `json:"scope"`
	}{*provenance, hex.EncodeToString(hash.Sum(nil)), detection, falsePositive, results, "not_evaluated", "Offline WAF only; no behavior, signed policy, customer representativeness, leakage review or production accuracy certification."}
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetIndent("", "  ")
	return encoder.Encode(evidence)
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
