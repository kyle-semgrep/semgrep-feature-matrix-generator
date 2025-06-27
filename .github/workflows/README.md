# 🤖 Automated Data Update Workflows

This directory contains GitHub Actions workflows that automatically keep your Feature Matrix Generator data up-to-date with the latest Semgrep capabilities.

## Available Workflows

### 1. Daily Updates (`update-data.yml`) 
**⭐ Recommended for most users**

- **Schedule**: Daily at 6 AM UTC
- **Behavior**: Direct commits to main branch
- **Best for**: Production repositories where you trust automated updates

**Features:**
- Runs both language and SCM update scripts
- Only commits when changes are detected
- Provides detailed execution summaries
- Manual trigger available via GitHub UI

### 2. Weekly Pull Requests (`weekly-update-pr.yml`)
**🔍 Best for review-first workflows**

- **Schedule**: Every Monday at 9 AM UTC  
- **Behavior**: Creates pull requests for review
- **Best for**: Teams that want to review changes before merging

**Features:**
- Creates feature branches for updates
- Detailed PR descriptions with change summaries
- Allows code review before data updates go live
- Automatic cleanup of branches after merge

### 3. Smart Updates (`smart-update.yml`)
**🧠 Best for critical production environments**

- **Schedule**: Twice daily (8 AM and 8 PM UTC)
- **Behavior**: Analyzes changes and creates GitHub Issues for significant updates
- **Best for**: When you need immediate notification of important changes

**Features:**
- Detects new languages or major feature changes
- Creates GitHub Issues for significant updates with action items
- Commits routine updates automatically
- Intelligent change analysis

## Setup Instructions

### 1. Choose Your Workflow(s)

Pick the workflow that matches your needs:
- **Just getting started?** → Use `update-data.yml`
- **Want review control?** → Use `weekly-update-pr.yml`  
- **Need change notifications?** → Use `smart-update.yml`

### 2. Repository Settings

Ensure your repository has the correct permissions:

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**

### 3. Customization Options

#### Adjust Schedules

Modify the `cron` expressions in any workflow:

```yaml
schedule:
  - cron: '0 6 * * *'  # Daily at 6 AM UTC
  - cron: '0 9 * * 1'  # Weekly on Monday at 9 AM UTC
  - cron: '0 8,20 * * *'  # Twice daily at 8 AM and 8 PM UTC
```

**Cron Helper:**
- `0 6 * * *` = Daily at 6 AM UTC
- `0 9 * * 1` = Every Monday at 9 AM UTC
- `0 */6 * * *` = Every 6 hours
- `0 0 1 * *` = First day of every month

#### Change Target Branch

Update the target branch in workflows (default is `main`):

```yaml
destination_branch: main  # Change to your default branch
```

#### Modify Python Version

Update Python version if needed:

```yaml
python-version: '3.9'  # Change to preferred version
```

## Manual Triggers

All workflows support manual execution:

1. Go to **Actions** tab in your repository
2. Select the workflow you want to run
3. Click **"Run workflow"** button
4. Choose branch and click **"Run workflow"**

## Monitoring Your Workflows

### View Execution History
- **Actions** tab → Select workflow → View run history
- Each run shows logs, execution time, and results

### Workflow Status Badges

Add status badges to your README:

```markdown
![Update Data](https://github.com/USERNAME/REPO/workflows/Update%20Feature%20Matrix%20Data/badge.svg)
![Weekly Updates](https://github.com/USERNAME/REPO/workflows/Weekly%20Data%20Update%20PR/badge.svg)
```

### Notifications

Set up notifications for workflow failures:
1. **Settings** → **Notifications** 
2. Enable **Actions** notifications
3. Choose email or GitHub notifications

## Troubleshooting

### Common Issues

**❌ Workflow fails with permission error**
- Solution: Check repository permissions (see Setup Instructions #2)

**❌ No changes detected but you expect updates**
- Check if your scripts are working locally: `python enrich_languages_with_semgrep_docs.py`
- Verify internet connectivity in Actions logs
- Check if Semgrep documentation URLs are accessible

**❌ Merge conflicts in automated PRs**
- Manual resolution required
- Merge main branch into the automated branch
- Consider using daily direct commits instead

### Debugging

Enable debug logging by adding this to any workflow:

```yaml
env:
  ACTIONS_RUNNER_DEBUG: true
  ACTIONS_STEP_DEBUG: true
```

## Security Considerations

These workflows:
- ✅ Only update JSON data files
- ✅ Use official GitHub Actions
- ✅ Don't expose secrets or sensitive data
- ✅ Only commit to your repository
- ✅ Run in isolated GitHub-hosted runners

## Next Steps

1. **Test your chosen workflow** by running it manually first
2. **Monitor the first few automated runs** to ensure everything works
3. **Customize schedules** to match your team's workflow
4. **Set up notifications** to stay informed of important changes

---

*These workflows will keep your Feature Matrix Generator current with the latest Semgrep capabilities, ensuring your presentations always have the most up-to-date information! 🚀* 