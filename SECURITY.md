# Security Policy

## 🔒 Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

- **Email**: security@aguide-ptbr.com.br
- **Response Time**: We aim to respond within 48 hours
- **Disclosure**: Please do not publicly disclose until we've addressed the issue

---

## 🛡️ Secure Configuration

### Environment Variables

This project uses environment variables to manage sensitive credentials:

| Variable | Description | Sensitivity |
|----------|-------------|-------------|
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | 🔴 High |
| `CONTENT_API_TOKEN` | Bearer token for content API | 🔴 High |
| `CONTENT_API_URL` | API endpoint URL | 🟡 Medium |

### Storage Best Practices

#### Local Development
- ✅ Store credentials in `.env` file (already in `.gitignore`)
- ✅ Never commit `.env` to version control
- ✅ Use `.env.example` as template (with placeholders only)

#### Production/CI/CD
- ✅ **Jenkins**: Use Jenkins Credentials Store with `withCredentials`
- ✅ **Docker**: Pass via environment variables, never bake into images
- ✅ **Cloud**: Use AWS Secrets Manager, Azure Key Vault, or similar

#### What NOT to do
- ❌ Never hardcode credentials in Python files
- ❌ Never commit `.env` files
- ❌ Never share credentials in logs, screenshots, or documentation
- ❌ Never use production credentials in development

---

## 🔐 Security Checklist

Before deploying to production, verify:

- [ ] All credentials loaded from environment variables
- [ ] `.env` file is in `.gitignore`
- [ ] No hardcoded API keys, tokens, or passwords in code
- [ ] `Config.validate()` called before pipeline execution
- [ ] Logging level set to `INFO` or higher (not `DEBUG`)
- [ ] API tokens have minimal required permissions
- [ ] Docker containers run as non-root user
- [ ] HTTPS used for all API communications

---

## 🔄 Credential Rotation

### Recommended Schedule
- **YouTube API Key**: Rotate every 90 days
- **Content API Token**: Rotate every 90 days or on team member departure

### Rotation Process
1. Generate new credentials in respective service
2. Update Jenkins Credentials Store (or your secret manager)
3. Deploy updated configuration
4. Verify pipeline runs successfully
5. Revoke old credentials after 24-48 hours grace period

---

## 📊 Security Monitoring

### What to Monitor
- Unauthorized API access attempts (check API logs)
- Quota exhaustion on YouTube API (possible credential leak)
- Failed authentication errors in pipeline logs
- Unusual geographic access patterns

### Alerts to Set Up
- ⚠️ YouTube API quota > 80% usage
- 🚨 Multiple authentication failures
- 🚨 API access from unexpected IP ranges

---

## 🧪 Security Testing

### Pre-Commit Checks
```bash
# Check for accidentally committed secrets
git diff --cached | grep -iE '(api[_-]?key|token|password|secret)'

# Verify .env is gitignored
git check-ignore .env && echo "✓ .env is gitignored" || echo "✗ WARNING: .env NOT gitignored!"
```

### Code Review Checklist
- [ ] No credentials in code
- [ ] All secrets loaded via `Config.from_env()`
- [ ] Validation called before using config
- [ ] Error messages don't expose sensitive data
- [ ] Logs don't contain tokens or API keys

---

## 📚 Compliance & Standards

This project follows:
- **OWASP API Security Top 10**: [https://owasp.org/www-project-api-security/](https://owasp.org/www-project-api-security/)
- **The Twelve-Factor App - Config**: [https://12factor.net/config](https://12factor.net/config)
- **CIS Docker Benchmark**: Non-root containers, minimal base images

---

## 🚨 Known Security Considerations

### 1. Logging at DEBUG Level
**Risk**: Debug logging may expose request headers containing Bearer tokens  
**Mitigation**: Never use `LOG_LEVEL=DEBUG` in production  
**Status**: Documented (not a vulnerability if used correctly)

### 2. API URL Exposure
**Risk**: API endpoint URL visible in docker-compose.yml  
**Mitigation**: Use environment variable override for sensitive deployments  
**Status**: Low risk for private repositories

---

## 📞 Contact & Support

- **Security Issues**: security@aguide-ptbr.com.br
- **General Support**: devops@aguide-ptbr.com.br
- **Documentation**: See [README.md](README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Last Updated**: January 31, 2026  
**Version**: 1.0.0
