#!/bin/bash
# CUDA-chan Setup Script

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║         CUDA-chan Setup Script                        ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}✗ Python version $PYTHON_VERSION is too old${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate venv
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Edit .env file and add your API keys!${NC}"
else
    echo -e "${YELLOW}.env file already exists (not overwriting)${NC}"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/cache data/logs data/screenshots
echo -e "${GREEN}✓ Data directories created${NC}"

# Check for tesseract
echo ""
echo "Checking for Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}⚠ Tesseract not found${NC}"
    echo "Install it with:"
    echo "  macOS:   brew install tesseract"
    echo "  Ubuntu:  sudo apt install tesseract-ocr"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
else
    echo -e "${GREEN}✓ Tesseract found${NC}"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║              Setup Complete!                          ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Install and run VTube Studio"
echo "3. Run: python main.py"
echo ""
echo "For detailed instructions, see SETUP_GUIDE.md"
echo ""
