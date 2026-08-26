package engine

import (
    "bytes"
    "encoding/json"
    "net/http"
    "time"
)

type RiskRequest struct {
    UserID    string                 `json:"user_id"`
    TenantID  string                 `json:"tenant_id"`
    IP        string                 `json:"ip"`
    Path      string                 `json:"path"`
    Method    string                 `json:"method"`
    Context   map[string]interface{} `json:"context"`
}

type RiskResponse struct {
    Score      float64 `json:"score"`
    Confidence float64 `json:"confidence"`
    Action     string  `json:"action"`
}

func CallRiskEngine(engineURL string, req RiskRequest) (*RiskResponse, error) {
    data, err := json.Marshal(req)
    if err != nil {
        return nil, err
    }

    client := &http.Client{Timeout: 2 * time.Second}
    resp, err := client.Post(engineURL+"/api/v1/risk/calculate", "application/json", bytes.NewBuffer(data))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result RiskResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    return &result, nil
}
