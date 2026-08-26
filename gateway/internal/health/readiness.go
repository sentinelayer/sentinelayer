package health

import (
    "encoding/json"
    "net/http"
)

type ReadinessResponse struct {
    Status string `json:"status"`
}

func ReadinessHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    _ = json.NewEncoder(w).Encode(ReadinessResponse{Status: "ready"})
}
