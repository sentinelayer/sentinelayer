package auth

default allow = false

allow {
    input.method == "GET"
    input.path == "/health"
}

allow {
    input.token_valid == true
    input.tenant_id == input.request_tenant
}

allow {
    input.is_admin == true
}
