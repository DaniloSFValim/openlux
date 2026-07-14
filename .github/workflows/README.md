# GitHub Actions CI/CD Pipelines

This directory contains automated workflows for testing, security, and deployment.

## Active Workflows

| Workflow | Trigger | Purpose | SLA |
|----------|---------|---------|-----|
| **ci.yml** | push / PR | Validate HTML, CSS, migrations + E2E tests | <12 min |
| **security-scan.yml** | push / PR / daily | npm audit, hardcoded secrets, OWASP ZAP, Snyk | ≤15 min |
| **e2e-tests.yml** | PR | 26 Playwright tests (detailed) | ≤10 min |
| **api-testing.yml** | PR | 9 Newman/Postman RPC requests | ≤5 min |
| **lighthouse-ci.yml** | PR | Performance & accessibility audit | ≤8 min |
| **backup.yml** | cron 02:00 UTC | Daily database backup → git | ≤5 min |
| **load-testing.yml** | manual | K6 load test against staging | — |

## Optimization Features (v2024.07)

### 🚀 Parallel Execution
- Jobs `validate` and `test` run in parallel (not sequentially)
- `check-changes` runs first to skip unnecessary test runs
- Saves **2–3 minutes** per build

### 💾 npm Cache
- Both jobs cache node_modules via `actions/cache@v4`
- Cache key includes `package-lock.json` hash
- Fallback to npm registry if cache miss
- Saves **30–60 seconds** per build

### 📚 Doc-only Skip
- Path filters: only run when code changes (not docs)
- `check-changes` job detects doc-only PRs
- Skip condition: `needs.check-changes.outputs.skip-tests == 'false'`
- Saves **2–5 minutes** for documentation-only PRs

### ⏱️ SLA Monitoring
- `sla-check` job monitors total build time
- Alert if build exceeds 12 minutes
- Outputs warning to Actions UI
- Helps identify performance regressions

## Running Locally

### E2E Tests
```bash
npm install @playwright/test
npx playwright test

# Run specific test
npx playwright test tests/e2e-basic.spec.js

# Debug mode
npx playwright test --debug
```

### Security Scan
```bash
npm audit
npm audit --json > npm-audit-report.json

# Check for hardcoded secrets
grep -r "BEGIN RSA PRIVATE KEY" .
grep -r "SUPABASE_SERVICE_ROLE_KEY" index.html
```

### HTML Validation
```bash
npm install html-validate
npx html-validate index.html
```

## Troubleshooting

### Build Time Exceeds SLA

**Symptom:** Workflow exceeds 12 minutes

**Diagnosis:**
1. Check Actions logs: GitHub → Repo → Actions → [Workflow] → [Run]
2. Identify slow step (usually E2E tests)
3. Check if tests are flaky (retry randomly failing tests)

**Fix:**
- Reduce test dataset size (use smaller sample)
- Parallelize E2E tests (split across multiple runners)
- Move slow tests to separate job (run on schedule, not every PR)

### Cache Miss on Every Run

**Symptom:** npm packages re-downloaded every build

**Diagnosis:**
```bash
# Check if package-lock.json is committed
git log --oneline package-lock.json | head -5

# Verify cache key consistency
echo ${{ hashFiles('**/package-lock.json') }}
```

**Fix:**
- Commit `package-lock.json` to git
- Ensure `npm ci` or `npm install --prefer-offline` in all jobs
- Clear cache if package versions changed: Actions → [Workflow] → Clear all caches

### Doc-only Skip Not Working

**Symptom:** Tests run even for README/docs-only changes

**Diagnosis:**
```bash
# Check what files changed
git diff --name-only origin/main...HEAD

# Verify path filter in PR event
# (only works for PR event, not push event)
```

**Fix:**
- Use PR event (not push) for doc-only detection
- Ensure changed files match regex in step logic
- Check branch name (must be to `main` or `develop`)

## Adding New Workflows

### Template
```yaml
name: My New Workflow
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  my-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Do something
        run: echo "Hello"
```

### Best Practices
1. ✅ Use `actions/checkout@v4` and `actions/setup-node@v4` (latest stable)
2. ✅ Add caching for expensive steps
3. ✅ Use `continue-on-error: true` for optional checks
4. ✅ Add concurrency limits if needed (prevent duplicate runs)
5. ✅ Document the workflow in this README

### Concurrency (Prevent Duplicate Runs)

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This cancels previous runs on the same branch.

## Performance Targets

| Check | Target | Current |
|-------|--------|---------|
| Validate (HTML/CSS) | <2 min | ~1 min |
| E2E Tests | <10 min | ~4 min |
| Security Scan | <15 min | ~8 min |
| **Total CI** | **<12 min** | **~6 min** |

## Related

- [DEPLOYMENT_GUIDE.md](../../docs/DEPLOYMENT_GUIDE.md) — Production deployment
- [TROUBLESHOOTING.md](../../TROUBLESHOOTING.md) — Common CI/CD issues
- [GitHub Actions Docs](https://docs.github.com/en/actions)
