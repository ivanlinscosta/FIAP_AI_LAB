#!/bin/bash
# ==========================================
# FIAP AI Lab - Railway Deploy Script
# ==========================================
# Run this after upgrading Railway plan and running: railway init --name FIAP-AI-Lab

set -e

echo "🚀 Starting FIAP AI Lab Railway Deploy..."
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install: curl -fsSL https://railway.com/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in. Run: railway login"
    exit 1
fi

# Check if project is linked
if ! railway status &> /dev/null; then
    echo "❌ No project linked. Run: railway init --name FIAP-AI-Lab"
    exit 1
fi

echo "✅ Railway CLI ready"
echo ""

# ==========================================
# Step 1: Create PostgreSQL
# ==========================================
echo "📦 Creating PostgreSQL service..."
railway add --database postgres --name fiap-postgres || echo "⚠️  PostgreSQL may already exist"
echo ""

# ==========================================
# Step 2: Create Gateway
# ==========================================
echo "🔧 Creating Gateway service..."
railway add --name fiap-ai-gateway || echo "⚠️  Gateway may already exist"
echo ""

# Wait for service to be ready
sleep 3

# ==========================================
# Step 3: Create n8n
# ==========================================
echo "📦 Creating n8n service..."
railway add --name fiap-n8n || echo "⚠️  n8n may already exist"
echo ""

# ==========================================
# Step 4: Create Dashboard
# ==========================================
echo "📊 Creating Dashboard service..."
railway add --name fiap-dashboard || echo "⚠️  Dashboard may already exist"
echo ""

echo "✅ All services created!"
echo ""
echo "Next steps:"
echo "1. Configure variables in Railway Dashboard"
echo "2. Set up Dockerfiles for each service"
echo "3. Generate public domains"
echo "4. Run: python3 scripts/provision_groups.py"
echo ""
echo "See docs/RAILWAY_DEPLOY.md for detailed instructions."
