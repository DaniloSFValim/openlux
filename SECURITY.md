# Security Policy

## 🔒 Reporting Security Vulnerabilities

**DO NOT** open a public GitHub issue for security vulnerabilities.

### Report Privately

📧 **Email:** [danilosfvalim@gmail.com](mailto:danilosfvalim@gmail.com)

**Include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Within 24 hours:** Acknowledgment
- **Within 48 hours:** Initial assessment
- **Within 7 days:** Fix or mitigation plan
- **Public disclosure:** Coordinated after fix is released

---

## 🛡️ Security Practices

This project follows these security practices:

### Frontend (HTML/JS)

- ✅ **XSS Prevention:** All user input escaped via `esc()` function
- ✅ **No Credentials:** Never hardcoded in frontend code
- ✅ **Secure Headers:** X-Frame-Options, X-Content-Type-Options via Netlify
- ✅ **HTTPS Only:** Enforced in production (Netlify)
- ✅ **CSP:** Content Security Policy via headers

### Backend (Supabase)

- ✅ **Row-Level Security:** All tables have RLS policies
- ✅ **JWT Authentication:** Email/password with secure tokens
- ✅ **SQL Injection Prevention:** PostgREST parameterized queries
- ✅ **Rate Limiting:** Handled by Supabase
- ✅ **Data Encryption:** In transit (HTTPS) and at rest (Supabase)

### Repository

- ✅ **No Secrets:** .env files in .gitignore
- ✅ **Branch Protection:** main branch protected
- ✅ **Code Review:** All PRs require review
- ✅ **CI/CD Checks:** Security scanning via GitHub Actions
- ✅ **Dependency Management:** Keep libraries updated

---

## 🔐 Known Security Considerations

### 1. Anon Key Exposure

**Issue:** `NEXT_PUBLIC_SUPABASE_ANON_KEY` is public (by design in SPA).

**Mitigation:**
- Anon key has limited permissions (RLS policies enforce access)
- Service Role Key is never exposed
- API rate limiting prevents abuse

### 2. CORS

**Issue:** SPA makes requests from browser (CORS visible).

**Mitigation:**
- Supabase CORS configured for domain
- Cookies HttpOnly (automatic in Supabase Auth)
- No sensitive data in error messages

### 3. Data Sensitivity

**Issue:** Infraestrutura pública (luminárias) — dados públicos.

**Mitigation:**
- No personal data (name, email) exposed publicly
- User emails protected by Auth role
- Admin actions logged in audit_logs

---

## 🧪 Testing Security

### Local Testing

```bash
# Check dependencies
npm audit

# Validate HTML/CSS
npm install -g html-validate
html-validate index.html

# Check for hardcoded secrets
grep -r "BEGIN PRIVATE" .
grep -r "password" .env*
```

### Production Validation

- [ ] HTTPS enabled
- [ ] Security headers present
- [ ] RLS policies enforced
- [ ] No console errors
- [ ] No sensitive data in localStorage

---

## 📋 Security Checklist for Contributors

Before submitting PR:

- [ ] No hardcoded credentials (.env, keys, tokens)
- [ ] No SQL injection risks (use PostgREST)
- [ ] No XSS (use `esc()` for user input)
- [ ] Input validation present
- [ ] Error messages don't leak info
- [ ] Dependencies are up to date
- [ ] No console.log() of sensitive data

---

## 📚 References

- [Supabase Security](https://supabase.com/docs/guides/auth)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

---

**Last Updated:** 2026-07-07
