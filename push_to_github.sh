#!/bin/bash
# Script to push repository to GitHub

echo "🚀 Pushing to GitHub repository: qa_bot"
echo ""

# Step 1: Set git user (if not already set)
echo "📝 Setting git user configuration..."
git config user.name "surbhiagrawal08" || echo "User name already set"
git config user.email "surbhiagrawal08@users.noreply.github.com" || echo "User email already set"

# Step 2: Update remote URL
echo "🔗 Updating remote URL..."
git remote set-url origin https://github.com/surbhiagrawal08/qa_bot.git

# Step 3: Verify remote
echo "✅ Current remote:"
git remote -v
echo ""

# Step 4: Clean up temporary files
echo "🧹 Cleaning up temporary files..."
rm -f test_doc.json test_questions.json frontend.html 2>/dev/null

# Step 5: Add all files
echo "📦 Adding files to git..."
git add .

# Step 6: Show what will be committed
echo "📋 Files to be committed:"
git status --short
echo ""

# Step 7: Commit
echo "💾 Committing changes..."
git commit -m "Complete QA Bot implementation with all evaluation criteria features

- FastAPI backend with LangChain QA service
- Support for PDF and JSON documents
- Error handling with file size and question limits
- Async/concurrent question processing
- Integration tests with mocked LLM
- Docker containerization support
- Structured JSON logging and metrics endpoint
- Minimal frontend UI
- Comprehensive documentation"

# Step 8: Push to GitHub
echo "🚀 Pushing to GitHub..."
echo "⚠️  You may be prompted for GitHub credentials"
git push -u origin main

echo ""
echo "✅ Done! Check your repository at: https://github.com/surbhiagrawal08/qa_bot"
