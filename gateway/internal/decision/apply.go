package decision

type Decision struct {
Action string
Reason string
}

func Apply(score float64) Decision {
if score >= 80 {
return Decision{Action: "BLOCK", Reason: "High risk score"}
} else if score >= 60 {
return Decision{Action: "CHALLENGE", Reason: "Medium risk score"}
} else if score >= 30 {
return Decision{Action: "MONITOR", Reason: "Low risk score"}
}
return Decision{Action: "ALLOW", Reason: "Normal traffic"}
}
