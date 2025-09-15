# Security Guidelines

## Credential Storage
- Store secrets outside the codebase. For local development, use a `.env` file that is excluded from version control.
- Never commit your `.env` file; add it to `.gitignore`.
- In production, rely on environment variables or a dedicated secrets manager (e.g., HashiCorp Vault, AWS Secrets Manager).

Example `.env` for local development:

```dotenv
# .env (development example - do NOT commit)
DATABASE_URL=sqlite:///local.db
API_KEY=dev-123456
```

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

## Key Rotation
- Establish a regular rotation policy for tokens and encryption keys (e.g., every 90 days).
- Automate rotations with scripts or CI jobs, such as a `rotate_keys.sh` script scheduled via cron.
- Update and distribute new keys securely and revoke old ones.

## Secret Scanning
- Integrate secret scanning tools into your workflow.
- Tools like [`git-secrets`](https://github.com/awslabs/git-secrets) can prevent committing credentials.
- Run scans locally and in CI to catch issues early.

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
