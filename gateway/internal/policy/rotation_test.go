package policy

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"testing"
)

func TestSigningKeyOverlapAndRevocation(t *testing.T) {
	client, oldKey, snapshot := fixture()
	newKey := ed25519.NewKeyFromSeed([]byte("rotation-test-seed-32-characters!")[:32])
	client.Keys["next"] = newKey.Public().(ed25519.PublicKey)
	if _, err := client.verify(signed(t, oldKey, snapshot), client.Now()); err != nil {
		t.Fatal(err)
	}
	snapshot.Version++
	payload, err := json.Marshal(snapshot)
	if err != nil {
		t.Fatal(err)
	}
	rotated, err := json.Marshal(Envelope{base64.StdEncoding.EncodeToString(payload), base64.StdEncoding.EncodeToString(ed25519.Sign(newKey, payload)), "next"})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := client.verify(rotated, client.Now()); err != nil {
		t.Fatal(err)
	}
	delete(client.Keys, "pinned")
	if _, err := client.verify(signed(t, oldKey, snapshot), client.Now()); err == nil {
		t.Fatal("revoked signer accepted")
	}
	if _, err := client.verify(rotated, client.Now()); err != nil {
		t.Fatal(err)
	}
}
