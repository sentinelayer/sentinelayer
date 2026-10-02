package policy

import (
	"os"
	"testing"
)

func TestVersionFloorSurvivesRestartAndRejectsCorruptState(t *testing.T) {
	directory := t.TempDir()
	c, key, s := fixture()
	if err := c.initState(directory); err != nil {
		t.Fatal(err)
	}
	if err := c.persistFloor(s.Version); err != nil {
		t.Fatal(err)
	}
	restarted, _, _ := fixture()
	if err := restarted.initState(directory); err != nil {
		t.Fatal(err)
	}
	older := s
	older.Version--
	if _, err := restarted.verify(signed(t, key, older), restarted.Now()); err == nil {
		t.Fatal("rollback survived restart")
	}
	if _, err := restarted.verify(signed(t, key, s), restarted.Now()); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(c.statePath, []byte("corrupt"), 0600); err != nil {
		t.Fatal(err)
	}
	fresh, _, _ := fixture()
	if err := fresh.initState(directory); err == nil {
		t.Fatal("corrupt state silently reset version floor")
	}
}
