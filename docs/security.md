# Security Guidelines

## Credential Storage
- Store secrets outside the codebase. For local development, use a `.env` file that is excluded from version control.
- In production, rely on environment variables or a dedicated secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager).

## Password Handling
- Never store plain-text passwords. Hash credentials with strong algorithms such as Argon2, bcrypt, or PBKDF2, each with a unique salt.
- Enforce strong password policies and enable multi-factor authentication where possible.

## Encryption
- Use TLS to encrypt network traffic.
- Encrypt sensitive data at rest with modern algorithms (e.g., AES-256) and rotate encryption keys regularly.
- Keep encryption keys in a secure key vault and restrict access.

## Token and API Key Usage
- Do not embed tokens or API keys in source code. Load them from environment variables or a secrets manager.
- Limit token scope and privileges; rotate and revoke keys on a schedule.
- Log and monitor token usage to detect anomalies.

## Permission Policies
- Apply the principle of least privilege to databases, services, and infrastructure.
- Implement role-based access control and audit access attempts.

## Secure Deployment Practices
- Keep dependencies and system packages up to date.
- Use HTTPS, security headers, and network firewalls.
- Scan containers and code for vulnerabilities before deployment.

## Development vs. Production
- Use separate credentials for development, staging, and production environments.
- In development, you may use placeholder secrets in a local `.env` file; do not reuse production credentials.
- In production, store secrets in managed services and enforce strict access controls and auditing.
