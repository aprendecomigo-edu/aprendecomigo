#!/bin/bash
# Setup script for Aprende Conmigo testing environment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Aprende Conmigo testing environment...${NC}"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is not installed. Please install Node.js and npm first.${NC}"
    exit 1
fi

# Check if python is installed
if ! command -v python &> /dev/null; then
    echo -e "${RED}python is not installed. Please install Python first.${NC}"
    exit 1
fi

# Install testing dependencies
echo -e "${YELLOW}Installing testing dependencies...${NC}"
cd "$(dirname "$0")/.." || exit
npm install

# Check if backend exists
if [ ! -d "../backend" ]; then
    echo -e "${RED}Backend directory not found. Please make sure you're running this script from the right location.${NC}"
    exit 1
fi

# Check if frontend exists
if [ ! -d "../frontend-ui" ]; then
    echo -e "${RED}Frontend directory not found. Please make sure you're running this script from the right location.${NC}"
    exit 1
fi

# Ensure backend fixtures directory exists
mkdir -p ../backend/fixtures

# Copy test fixtures to backend
echo -e "${YELLOW}Copying test fixtures to backend...${NC}"
cp -r backend/fixtures/* ../backend/fixtures/ 2>/dev/null || :

# Create symlinks from testing utilities to backend and frontend
echo -e "${YELLOW}Creating symlinks for test utilities...${NC}"

# Create backend test utils symlink
if [ ! -d "../backend/test_utils" ]; then
    ln -sf "$(pwd)/backend" "../backend/test_utils"
    echo -e "${GREEN}Created symlink to backend test utilities${NC}"
fi

# Create frontend test utils symlink
if [ ! -d "../frontend-ui/test-utils" ]; then
    ln -sf "$(pwd)/frontend" "../frontend-ui/test-utils"
    echo -e "${GREEN}Created symlink to frontend test utilities${NC}"
fi

# Explain how to run tests
echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To run backend tests:${NC}"
echo -e "  cd ../backend"
echo -e "  python manage.py test"
echo -e "${YELLOW}To run frontend tests:${NC}"
echo -e "  cd ../frontend-ui"
echo -e "  npm test"
echo -e "${YELLOW}To run E2E tests:${NC}"
echo -e "  cd $(pwd)"
echo -e "  npm run prepare:e2e"
echo -e "  npm run e2e:build:ios && npm run e2e:test:ios"
echo -e "${YELLOW}To run API integration tests:${NC}"
echo -e "  cd $(pwd)"
echo -e "  node integration/api-tests/auth-flow.test.js"
echo -e "\n${GREEN}Happy testing!${NC}"
