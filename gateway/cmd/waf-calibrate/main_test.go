package main

import (
	"github.com/sentinelayer/gateway/internal/waf"
	"strings"
	"testing"
)

func TestConfidenceBoundsDoNotCertifyTinyPerfectCorpus(t *testing.T) {
	detected := measure(10, 10)
	fp := measure(0, 10)
	if detected.Interval[0] >= .95 || fp.Interval[1] <= .05 {
		t.Fatal("tiny perfect corpus must not establish production accuracy targets")
	}
	if measure(0, 0).Estimate != nil {
		t.Fatal("missing label class must not become a zero rate")
	}
}
func TestEvaluationLabelsAndRejectsInvalidOrDuplicateCases(t *testing.T) {
	engine, err := waf.NewEngine("../../../waf/rules")
	if err != nil {
		t.Fatal(err)
	}
	corpus := `{"id":"a","label":"attack","path":"/search?q=%27+OR+1%3D1+--+"}` + "\n" + `{"id":"b","label":"benign","path":"/search?q=hello"}`
	rows, detection, fp, err := evaluate(strings.NewReader(corpus), engine)
	if err != nil || len(rows) != 2 || detection.Events != 1 || fp.Events != 0 {
		t.Fatalf("classification failed: %v", err)
	}
	for _, bad := range []string{`{"id":"a","label":"unknown"}`, `{"id":"a","label":"benign","path":"http://example.test"}`, `{"id":"a","label":"benign","extra":true}`, corpus + "\n" + `{"id":"a","label":"benign"}`, `{"id":"a","label":"benign"} {}`} {
		if _, _, _, err := evaluate(strings.NewReader(bad), engine); err == nil {
			t.Fatal("invalid corpus accepted")
		}
	}
}
