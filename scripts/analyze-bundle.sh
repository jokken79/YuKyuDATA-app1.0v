#!/bin/bash

# Bundle Analysis Script for TAREA 6
# Analyzes webpack bundle size and provides optimization recommendations

set -e

echo "=================================================="
echo "YuKyu Frontend Bundle Analysis"
echo "TAREA 6 - Bundle Optimization"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules not found. Running npm install...${NC}"
    npm install
fi

# Build webpack bundle with analysis
echo ""
echo "Building webpack bundle with size analysis..."
echo ""

# Remove previous dist folder
rm -rf dist

# Build with NODE_ENV=production and ANALYZE flag
ANALYZE=true NODE_ENV=production npx webpack --config webpack.config.js 2>&1

# Check if build succeeded
if [ ! -d "dist" ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# Calculate sizes
echo ""
echo "=================================================="
echo "Bundle Size Analysis"
echo "=================================================="
echo ""

# Function to convert bytes to human-readable format
bytes_to_human() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$(echo "scale=2; $bytes / 1024" | bc)KB"
    else
        echo "$(echo "scale=2; $bytes / 1048576" | bc)MB"
    fi
}

# Analyze main bundle
echo "Main Bundle Files:"
echo "────────────────────────────────────"

total_js=0
total_css=0
total_all=0

for file in dist/*.js dist/*.css; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        filename=$(basename "$file")

        # Get gzip size
        gzip_size=$(gzip -c "$file" | wc -c)

        echo "  $filename"
        echo "    Raw:  $(bytes_to_human $size)"
        echo "    Gzip: $(bytes_to_human $gzip_size)"

        if [[ "$file" == *.js ]]; then
            total_js=$((total_js + size))
        else
            total_css=$((total_css + size))
        fi

        total_all=$((total_all + size))
    fi
done

echo ""
echo "Chunk Files:"
echo "────────────────────────────────────"

for file in dist/*.chunk.js dist/*.chunk.css; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        filename=$(basename "$file")

        gzip_size=$(gzip -c "$file" | wc -c)

        echo "  $filename"
        echo "    Raw:  $(bytes_to_human $size)"
        echo "    Gzip: $(bytes_to_human $gzip_size)"

        total_all=$((total_all + size))
    fi
done

echo ""
echo "Total Bundle Size:"
echo "────────────────────────────────────"
echo "  JavaScript: $(bytes_to_human $total_js)"
echo "  CSS:        $(bytes_to_human $total_css)"
echo "  Total:      $(bytes_to_human $total_all)"

echo ""
echo "=================================================="
echo "Performance Metrics"
echo "=================================================="
echo ""

# Check against targets
target_js=176000  # 176 KB minified
target_gzip=54000 # 54 KB gzip

if [ $total_js -lt $target_js ]; then
    echo -e "${GREEN}✓ JavaScript within target (< 176 KB)${NC}"
else
    echo -e "${YELLOW}⚠ JavaScript exceeds target (${target_js} bytes)${NC}"
fi

# Estimate bundle analyzer output
if [ -f "dist/bundle-report.html" ]; then
    echo ""
    echo "Bundle Report:"
    echo "  Location: dist/bundle-report.html"
    echo "  Open in browser for detailed analysis"
fi

echo ""
echo "=================================================="
echo "Recommendations"
echo "=================================================="
echo ""
echo "1. Review dist/bundle-report.html for detailed breakdown"
echo "2. Check webpack chunk groups are properly isolated"
echo "3. Verify tree-shaking is working (no unused code)"
echo "4. Consider lazy-loading less critical chunks"
echo ""

echo -e "${GREEN}Bundle analysis complete!${NC}"
