# GitHub Secrets Setup Guide

## Quick Setup

Copy this checklist to your GitHub repository settings and complete each step.

## 1. Create SSH Key for Deployment

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -f ~/.ssh/github-deploy-key -C "github-ci-deployment"

# Add public key to your server
ssh-copy-id -i ~/.ssh/github-deploy-key.pub user@your-server.com

# Encode private key in base64
cat ~/.ssh/github-deploy-key | base64 | tr -d '\n'
```

## 2. Add Repository Secrets

Go to: **GitHub Repository** → **Settings** → **Secrets and variables** → **Actions**

### 2.1 Deployment Secrets (Required for deployment workflow)

| Secret Name | Value | How to Get |
|---|---|---|
| `DEPLOY_HOST` | Your production server IP or hostname | `your-server.com` or `192.168.1.1` |
| `DEPLOY_USER` | SSH username for deployment | Same as `ssh user@host` |
| `DEPLOY_KEY` | Base64-encoded SSH private key | Output from command above |

### 2.2 Docker Hub Secrets (Required for pushing images to DockerHub)

| Secret Name | Value | How to Get |
|---|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | https://hub.docker.com/settings/account |
| `DOCKERHUB_TOKEN` | Docker Hub access token | https://hub.docker.com/settings/security → **New Access Token** |

### 2.3 SonarCloud (Optional - for code quality)

| Secret Name | Value | How to Get |
|---|---|---|
| `SONAR_TOKEN` | SonarCloud authentication token | https://sonarcloud.io/account/security/ |

## 3. Step-by-Step Secret Creation

### Creating DEPLOY_KEY

1. Generate the base64-encoded key:
```bash
cat ~/.ssh/github-deploy-key | base64 | tr -d '\n' | pbcopy
# (On Linux: ... | xclip -selection clipboard)
```

2. Go to **GitHub Secrets**
3. Click **New repository secret**
4. Name: `DEPLOY_KEY`
5. Value: Paste the base64 string
6. Click **Add secret**

### Creating DOCKERHUB_TOKEN

1. Go to https://hub.docker.com/settings/security
2. Click **New Access Token**
3. Name: `github-actions`
4. Click **Generate**
5. Copy the token (won't be shown again!)
6. Go to **GitHub Secrets**
7. Click **New repository secret**
8. Name: `DOCKERHUB_TOKEN`
9. Value: Paste the token
10. Click **Add secret**

### Creating SONAR_TOKEN

1. Go to https://sonarcloud.io (sign in with GitHub)
2. Go to **Account** → **Security**
3. Generate new token
4. Go to **GitHub Secrets**
5. Click **New repository secret**
6. Name: `SONAR_TOKEN`
7. Value: Paste the token
8. Click **Add secret**

## 4. Test Your Secrets

### Test SSH Connection

```bash
# Verify your SSH key works
ssh -i ~/.ssh/github-deploy-key user@your-server.com "whoami"

# Output should show your username
```

### Test Docker Hub Credentials

```bash
docker login -u YOUR_USERNAME -p YOUR_TOKEN
docker pull YOUR_USERNAME/any-public-image:latest
```

## 5. Verify Configuration

### Check GitHub Actions Status

1. Go to your repository
2. Click **Actions** tab
3. You should see workflow files listed:
   - backend-tests.yml
   - frontend-tests.yml
   - docker-build.yml
   - security-scan.yml
   - deploy.yml
   - health-check.yml

### Run a Test Workflow

1. Create a new branch: `git checkout -b test-ci`
2. Make a small change (e.g., add a comment)
3. Commit and push: `git push origin test-ci`
4. Go to **Actions** tab
5. You should see workflows running
6. Check logs for any errors

## 6. Branch Protection Rules (Recommended)

To enforce passing CI/CD checks before merge:

1. Go to **Settings** → **Branches**
2. Click **Add rule** under **Branch protection rules**
3. Branch name pattern: `main`
4. Check:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
5. Select required status checks:
   - `test` (backend-tests)
   - `test` (frontend-tests)
   - `build` (docker-build)
6. Click **Create** → **Save changes**

## 7. CI/CD Workflow Triggers

### When Do Workflows Run?

| Workflow | Trigger | Branches |
|---|---|---|
| Backend Tests | Push or PR + backend changes | main, develop |
| Frontend Tests | Push or PR + frontend changes | main, develop |
| Docker Build | Push or PR + Docker changes | main, develop |
| Security Scan | Push or PR | main, develop |
| Deploy | Push only | main |
| Health Check | Every 6 hours (scheduled) | - |

### Force Workflow Run

```bash
# Create empty commit to trigger workflows
git commit --allow-empty -m "Trigger CI/CD workflows"
git push
```

## 8. Monitoring & Notifications

### Enable Email Notifications

1. Go to **Settings** → **Notifications**
2. Check **GitHub Actions** notification preferences
3. Choose email address

### Add Slack Notifications (Optional)

Add to any workflow YAML:

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

Then add `SLACK_WEBHOOK` secret with your Slack webhook URL.

## 9. Troubleshooting

### Secret Not Working

```bash
# Verify secret exists in GitHub UI
# Settings → Secrets and variables → Actions → Look for your secret

# Check workflow syntax
# Actions tab → Click workflow → Check logs
```

### SSH Connection Failed

```bash
# Test SSH locally first
ssh -i ~/.ssh/github-deploy-key -v user@host

# Check SSH key permissions
chmod 600 ~/.ssh/github-deploy-key
chmod 644 ~/.ssh/github-deploy-key.pub

# Verify public key on server
cat ~/.ssh/authorized_keys | grep github-deploy-key
```

### Docker Push Failed

```bash
# Test locally
docker login -u USERNAME -p TOKEN
docker tag app:latest USERNAME/app:latest
docker push USERNAME/app:latest

# Check DockerHub token hasn't expired
# Settings → Security → Regenerate if needed
```

## 10. Security Best Practices

✅ **DO:**
- Rotate SSH keys regularly
- Use personal access tokens instead of passwords
- Set expiration dates on tokens
- Review action logs for suspicious activity
- Use branch protection rules
- Enable 2FA on GitHub account

❌ **DON'T:**
- Commit secrets to repository
- Share secrets in issues/PRs
- Use the same secret for multiple services
- Store secrets in plaintext files
- Push private SSH keys

## 11. Next Steps

1. ✅ Generate SSH key
2. ✅ Create GitHub Secrets
3. ✅ Configure Branch Protection Rules
4. ✅ Test by pushing to a branch
5. ✅ Monitor first workflow run
6. ✅ Adjust as needed

## Support

For issues:
- Check GitHub Actions logs: **Actions** tab → Click workflow → View logs
- Review secret names (case-sensitive)
- Verify paths in workflow files match your project structure
- Check workflow syntax: `docker run --rm -v $(pwd):/repo actionlint/actionlint`

