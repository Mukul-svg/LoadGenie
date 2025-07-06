#!/bin/bash

# LoadGenie K6 Runner Setup Script
# This script sets up the development environment for the K6 runner service

set -e

echo "🚀 LoadGenie K6 Runner Setup"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_status "Detected OS: $OS"

# Check if k6 is already installed
if command -v k6 &> /dev/null; then
    K6_VERSION=$(k6 version | head -n1)
    print_status "K6 already installed: $K6_VERSION"
else
    echo "📦 Installing K6..."
    
    if [[ "$OS" == "linux" ]]; then
        # Install k6 on Linux
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo gpg -k
            sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
            echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
            sudo apt-get update
            sudo apt-get install k6
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install https://dl.k6.io/rpm/repo.rpm
            sudo dnf install k6
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install https://dl.k6.io/rpm/repo.rpm
            sudo yum install k6
        else
            print_warning "Package manager not recognized. Installing k6 via binary download..."
            # Download binary directly
            K6_VERSION="v0.47.0"
            wget -O /tmp/k6.tar.gz "https://github.com/grafana/k6/releases/download/${K6_VERSION}/k6-${K6_VERSION}-linux-amd64.tar.gz"
            tar -xzf /tmp/k6.tar.gz -C /tmp
            sudo mv /tmp/k6-${K6_VERSION}-linux-amd64/k6 /usr/local/bin/
            rm -rf /tmp/k6*
        fi
    elif [[ "$OS" == "macos" ]]; then
        # Install k6 on macOS
        if command -v brew &> /dev/null; then
            brew install k6
        else
            print_error "Homebrew not found. Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    fi
    
    # Verify installation
    if command -v k6 &> /dev/null; then
        K6_VERSION=$(k6 version | head -n1)
        print_status "K6 installed successfully: $K6_VERSION"
    else
        print_error "K6 installation failed"
        exit 1
    fi
fi

# Check Python dependencies
echo "🐍 Checking Python dependencies..."

if ! python3 -c "import fastapi" &> /dev/null; then
    print_warning "FastAPI not found. Installing dependencies..."
    pip install -r requirements.txt
fi

print_status "Python dependencies verified"

# Create necessary directories
echo "📁 Creating directories..."

mkdir -p /tmp/k6_results
mkdir -p logs

print_status "Directories created"

# Set up environment variables
echo "🔧 Setting up environment..."

if [[ ! -f .env ]]; then
    cat > .env << EOF
# LoadGenie Environment Configuration

# Server settings
DEBUG=true
HOST=0.0.0.0
PORT=8000

# AI Service (Gemini)
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.8
AI_MAX_RETRIES=3
AI_TIMEOUT=60

# K6 Runner settings
K6_RESULTS_DIR=/tmp/k6_results
K6_TIMEOUT=300

# Database
DATABASE_URL=sqlite:///./loadgenie.db

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=*
EOF
    print_warning "Created .env file. Please update GEMINI_API_KEY with your actual API key."
else
    print_status "Environment file already exists"
fi

# Test the K6 installation
echo "🧪 Testing K6 installation..."

cat > /tmp/test_k6.js << 'EOF'
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    vus: 1,
    duration: '3s',
};

export default function() {
    const response = http.get('https://httpbin.org/get');
    check(response, {
        'status is 200': (r) => r.status === 200,
    });
}
EOF

if k6 run /tmp/test_k6.js --summary-export=/tmp/test_summary.json > /dev/null 2>&1; then
    print_status "K6 test execution successful"
    rm -f /tmp/test_k6.js /tmp/test_summary.json
else
    print_error "K6 test execution failed"
    exit 1
fi

# Test the Python service
echo "🐍 Testing Python service..."

if python3 -c "
import sys
sys.path.append('.')
from app.services.k6_runner import K6Runner
from app.services.ai_service import AIService
print('✅ Python service imports successful')
" 2>/dev/null; then
    print_status "Python service test successful"
else
    print_warning "Python service test failed - make sure to set GEMINI_API_KEY"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Update your GEMINI_API_KEY in the .env file"
echo "2. Start the development server:"
echo "   cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Test the API endpoints:"
echo "   curl http://localhost:8000/api/v1/test/health"
echo ""
echo "4. Run the demo script:"
echo "   cd backend && python3 scripts/demo_k6_runner.py"
echo ""
echo "5. Run integration tests:"
echo "   cd backend && python3 tests/test_integration_k6.py"
echo ""
echo "📚 API Documentation will be available at: http://localhost:8000/docs"
