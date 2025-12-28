# CI/CD Pipeline Overview

## What is CI/CD?

**CI/CD** (Continuous Integration / Continuous Deployment) is an automated system that:

- **Continuous Integration (CI)**: Automatically tests code when you push changes
- **Continuous Deployment (CD)**: Automatically deploys tested code to production

## Your CI/CD Pipeline

This project uses **GitHub Actions** to automatically:

### 1. Test Backend Code
- Runs on Python 3.11
- Tests with pytest
- Checks code style with flake8
- Runs against a PostgreSQL database

### 2. Test Frontend Code
- Runs on Node 18.x and 20.x
- Builds TypeScript
- Runs ESLint (if configured)
- Tests components (if configured)

### 3. Build Docker Images
- Builds backend Docker image
- Builds frontend Docker image
- Validates docker-compose configuration
- Optionally pushes to Docker Hub

### 4. Security Scanning
- Scans for vulnerabilities (Trivy)
- Checks for exposed secrets (GitLeaks)
- Code quality analysis (SonarCloud - optional)

### 5. Deploy to Production
- Pulls latest code
- Updates Docker images
- Restarts services
- Runs database migrations

### 6. Health Checks
- Runs every 6 hours
- Verifies API is responding
- Verifies Frontend is responding

## Quick Start

### 1. Minimal Setup (Tests Only)

No additional configuration needed! Workflows automatically run on:
- Every push to `main` or `develop`
- Every pull request

Check **Actions** tab to see results.

### 2. Full Setup (With Deployment)

Follow [GITHUB_SECRETS_SETUP.md](./GITHUB_SECRETS_SETUP.md) to configure:

```
Required Secrets:
✓ DEPLOY_HOST (your server IP/hostname)
✓ DEPLOY_USER (SSH username)
✓ DEPLOY_KEY (SSH private key)
✓ DOCKERHUB_USERNAME (optional but recommended)
✓ DOCKERHUB_TOKEN (optional but recommended)
```

## Workflow Files

Located in `.github/workflows/`:

| File | Purpose | Trigger |
|------|---------|---------|
| `backend-tests.yml` | Test backend code | Push/PR to backend/ |
| `frontend-tests.yml` | Test frontend code | Push/PR to frontend/ |
| `docker-build.yml` | Build Docker images | Push/PR to Docker files |
| `security-scan.yml` | Security & code quality | Every push/PR |
| `deploy.yml` | Deploy to production | Push to main only |
| `health-check.yml` | Monitor production | Every 6 hours |

## How to Use

### View Workflow Results

1. Go to your repository
2. Click **Actions** tab
3. Click a workflow run to see details
4. Click a job to see logs

### Run a Workflow Manually

1. Go to **Actions** tab
2. Click a workflow (e.g., "Backend Tests & Linting")
3. Click **Run workflow** button
4. Select branch and click **Run workflow**

### Check Branch Protection Status

When creating a pull request:
- Red X = Tests failing (can't merge)
- Green ✓ = Tests passing (can merge)
- Orange ⏳ = Tests still running

## Automatic Actions

### On Every Push to `develop`

1. ✅ Run backend tests
2. ✅ Run frontend tests
3. ✅ Build Docker images
4. ✅ Security scan
5. ⏸️ (No deployment - only on `main`)

### On Every Push to `main`

1. ✅ Run all tests
2. ✅ Build Docker images
3. ✅ Push to Docker Hub
4. ✅ Security scan
5. ✅ **Deploy to production** (if configured)
6. ✅ Run database migrations

### Every 6 Hours

1. ✅ Check API health
2. ✅ Check Frontend health
3. ⚠️ Alert if services down

## Common Issues

### Workflow Not Running

**Problem**: Pushed code but workflow didn't start

**Solution**:
1. Check path filters (e.g., `frontend/` changes only trigger frontend tests)
2. Verify workflows are enabled: **Actions** → Enable workflows
3. Check branch name (workflows only run on `main` and `develop`)

### Tests Failing

**Problem**: Workflow shows red X (tests failed)

**Solution**:
1. Click workflow to see logs
2. Scroll to failed test
3. Read error message
4. Fix code locally and push again

### Can't Deploy

**Problem**: "Deploy" job is skipped

**Solution**:
1. Make sure you're pushing to `main` branch
2. Verify GitHub Secrets are configured
3. Check SSH key works: `ssh -i key user@host "whoami"`
4. Review deploy logs for error details

## Environment Variables

### Available in All Workflows

```yaml
github.repository        # owner/repo
github.ref              # refs/heads/branch-name
github.sha              # commit hash
github.actor            # who triggered the workflow
github.event_name       # push, pull_request, schedule, etc.
```

### Custom Secrets

Available as `${{ secrets.SECRET_NAME }}`:
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_KEY`
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SONAR_TOKEN` (optional)

## Performance Tips

### Speed Up Tests

1. **Use caching**:
   ```yaml
   - uses: actions/setup-python@v4
     with:
       cache: 'pip'
   ```

2. **Parallel jobs**: Jobs run simultaneously by default

3. **Skip workflows**:
   ```bash
   git commit -m "Update docs [skip ci]"
   ```
   The `[skip ci]` prevents workflow from running

### Reduce Docker Build Time

- Docker uses layer caching automatically
- Smaller base images (alpine, slim variants)
- Minimal dockerfiles (no unnecessary RUN commands)

## Notifications

### Email
GitHub sends emails for:
- Workflow failures
- Deployment completions
- CI alerts

**Configure**: Settings → Notifications

### Slack (Optional)

1. Create Slack webhook
2. Add `SLACK_WEBHOOK` secret
3. Workflows can send messages

### GitHub Status Checks

PR shows ✓ or ✗ for each check - this is automatic!

## Documentation

- **Full Guide**: See [CI_CD_GUIDE.md](./CI_CD_GUIDE.md)
- **Secrets Setup**: See [GITHUB_SECRETS_SETUP.md](./GITHUB_SECRETS_SETUP.md)

## Examples

### Test Only (No Deployment)

```bash
git checkout -b feature/new-feature
# Make changes
git push origin feature/new-feature

# GitHub Actions automatically:
✓ Runs tests
✓ Reports results in PR
# You merge when tests pass
```

### Deploy to Production

```bash
git checkout main
git pull origin main
git merge feature/new-feature
git push origin main

# GitHub Actions automatically:
✓ Run all tests
✓ Build Docker images
✓ Push to Docker Hub
✓ SSH into server
✓ Pull new images
✓ Restart services
✓ Run migrations
✓ Verify health
```

## Next Steps

1. **Read** [CI_CD_GUIDE.md](./CI_CD_GUIDE.md) for detailed workflow info
2. **Configure** secrets following [GITHUB_SECRETS_SETUP.md](./GITHUB_SECRETS_SETUP.md)
3. **Push** a test change to trigger workflows
4. **Monitor** **Actions** tab to see results
5. **Enable** branch protection rules (recommended)

## Support

For issues, check:
1. **Actions** tab → Click workflow → Review logs
2. Secret names (case-sensitive!)
3. SSH key permissions
4. Docker Hub credentials
5. Workflow syntax

