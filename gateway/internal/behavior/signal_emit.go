package behavior

type Signal struct {
    Type    string
    TenantID string
    Data    map[string]interface{}
}

func EmitSignal(signal Signal) {
    // Placeholder for signal emission
}
