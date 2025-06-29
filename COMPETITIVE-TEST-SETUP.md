# Competitive Intelligence Test Deployment

## Overview
This document explains how to test the competitive intelligence features using a separate GitHub Pages deployment.

## How It Works

### Test Branch Setup
- **Source Branch**: `competitive-intelligence` (where you develop new features)
- **Test Branch**: `github-pages-test` (automatically created for testing)
- **Production Branch**: `github-pages` (existing main deployment)

### Test Deployment Process

1. **Automatic Deployment**: When you push to the `competitive-intelligence` branch, the GitHub Action automatically:
   - Creates or updates the `github-pages-test` branch
   - Merges your competitive intelligence changes
   - Adds a visual banner to indicate it's the test version
   - Pushes the test version to the `github-pages-test` branch

2. **Visual Indicators**: The test site includes:
   - Orange banner at the top: "🧪 COMPETITIVE INTELLIGENCE TEST VERSION"
   - Same functionality as main site but with new competitive features

## Accessing Your Test Site

### Option 1: Configure GitHub Pages Settings (Recommended)
1. Go to your repository settings
2. Navigate to "Pages" section
3. Temporarily change the source branch from `github-pages` to `github-pages-test`
4. Your test site will be available at: `https://kyle-semgrep.github.io/semgrep-feature-matrix-generator/`
5. When done testing, switch back to `github-pages` branch for production

### Option 2: Manual Testing
- The `github-pages-test` branch contains all your test files
- You can download and run locally for testing

## Testing Workflow

1. **Make Changes**: Work on the `competitive-intelligence` branch
2. **Auto-Deploy**: Push changes triggers automatic test deployment
3. **Visual Test**: View your changes with the test banner
4. **Iterate**: Make more changes and push again for updated test deployment
5. **Merge**: When satisfied, merge `competitive-intelligence` → `main` for production

## Files Changed

### New Workflow
- `.github/workflows/deploy-competitive-test.yml` - Handles test deployments

### Branch Structure
```
main                    → github-pages (production)
competitive-intelligence → github-pages-test (testing)
```

## Next Steps

To start testing:
1. Make some changes to the competitive intelligence features
2. Push to the `competitive-intelligence` branch  
3. Check the GitHub Actions tab to see the deployment
4. Configure GitHub Pages to use `github-pages-test` branch
5. Visit your test site with the orange banner

## Troubleshooting

- **Action Fails**: Check the Actions tab for detailed logs
- **No Test Site**: Ensure GitHub Pages is configured to use `github-pages-test` branch
- **No Banner**: The banner is added automatically during deployment
- **Merge Conflicts**: The action will auto-resolve by favoring the competitive-intelligence branch

## Cleanup

When you're done testing and have merged to production:
- Switch GitHub Pages back to `github-pages` branch
- Optionally delete the `github-pages-test` branch if no longer needed