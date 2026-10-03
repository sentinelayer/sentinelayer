package policy

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"log"
	"os"
	"path/filepath"
)

type versionState struct {
	PolicyID string `json:"policy_id"`
	TenantID string `json:"tenant_id"`
	Version  int    `json:"version"`
}

func (c *Client) initState(directory string) error {
	if directory == "" {
		return nil
	}
	if err := os.MkdirAll(directory, 0700); err != nil {
		return errors.New("cannot create policy state directory")
	}
	info, err := os.Lstat(directory)
	if err != nil || !info.IsDir() || info.Mode().Perm()&0022 != 0 {
		return errors.New("policy state directory must be a real directory without group/world write access")
	}
	digest := sha256.Sum256([]byte(c.TenantID + "\x00" + c.PolicyID))
	c.statePath = filepath.Join(directory, hex.EncodeToString(digest[:])+".json")
	info, err = os.Lstat(c.statePath)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil || !info.Mode().IsRegular() || info.Mode().Perm()&0022 != 0 || info.Size() > 4096 {
		return errors.New("unsafe policy version state file")
	}
	raw, err := os.ReadFile(c.statePath)
	if err != nil || len(raw) > 4096 {
		return errors.New("cannot read policy version state")
	}
	var state versionState
	if strictDecode(raw, &state) != nil || state.PolicyID != c.PolicyID || state.TenantID != c.TenantID || state.Version < 1 {
		return errors.New("invalid policy version state")
	}
	c.floor = state.Version
	log.Printf("Loaded durable policy version floor: policy=%s version=%d", c.PolicyID, c.floor)
	return nil
}

// persistFloor writes before a newly verified version can enter the active cache.
// The directory must belong to one gateway process on a durable volume.
func (c *Client) persistFloor(version int) error {
	if version <= c.floor {
		return nil
	}
	if c.statePath != "" {
		raw, err := json.Marshal(versionState{c.PolicyID, c.TenantID, version})
		if err != nil {
			return err
		}
		file, err := os.CreateTemp(filepath.Dir(c.statePath), ".policy-state-*")
		if err != nil {
			return errors.New("cannot persist policy version")
		}
		name := file.Name()
		defer os.Remove(name)
		if _, err = file.Write(raw); err != nil {
			file.Close()
			return err
		}
		if err = file.Sync(); err != nil {
			file.Close()
			return err
		}
		if err = file.Close(); err != nil {
			return err
		}
		if err = os.Rename(name, c.statePath); err != nil {
			return err
		}
		directory, err := os.Open(filepath.Dir(c.statePath))
		if err != nil {
			return err
		}
		defer directory.Close()
		if err = directory.Sync(); err != nil {
			return err
		}
	}
	c.floor = version
	return nil
}
