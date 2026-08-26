package behavior

import (
"bytes"
"encoding/json"
"log"
"net/http"
"os"
"time"
)

type Signal struct {
Type     string                 `json:"type"`
TenantID string                 `json:"tenant_id"`
Data     map[string]interface{} `json:"data"`
}

func EmitSignal(signal Signal) {
payload, err := json.Marshal(signal)
if err != nil {
log.Printf("behavior signal marshal error: %v", err)
return
}
log.Printf("behavior_signal type=%s tenant=%s", signal.Type, signal.TenantID)
url := os.Getenv("BEHAVIOR_INGEST_URL")
if url == "" {
return
}
client := &http.Client{Timeout: 100 * time.Millisecond}
req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(payload))
if err != nil {
return
}
req.Header.Set("Content-Type", "application/json")
resp, err := client.Do(req)
if err != nil {
log.Printf("behavior signal emit failed: %v", err)
return
}
_ = resp.Body.Close()
}
