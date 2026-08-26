# ROPA Template

| Processing Activity | Purpose | Data Categories | Subjects | Recipients | Retention | Transfer |
|----------------------|---------|----------------|----------|------------|-----------|----------|
| User Registration | Account creation | PII, Email | Users | Internal | 7 years | None |
| API Request Processing | Security enforcement | Request data | Customers | Gateway | 30 days | None |
| Incident Management | Security response | Incident data | Tenants | Internal | 7 years | None |

# DPIA Template

| Assessment Area | Risk Level | Mitigation |
|-----------------|------------|------------|
| Data Collection | Medium | Minimize PII |
| Data Storage | High | Encryption |
| Data Transfer | Low | TLS 1.3 |
| Data Retention | Medium | Automated deletion |
| User Rights | Medium | Access/Deletion API |
