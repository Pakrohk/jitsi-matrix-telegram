#!/bin/bash
# Build maubot plugin package

set -e

PLUGIN_DIR="src/adapters/maubot"
OUTPUT="jitsi-bot.mbp"

echo "Building maubot plugin..."

# Clean old build
rm -f "$OUTPUT"

# Create .mbp (zip file)
cd "$PLUGIN_DIR"
zip -9r "../../$OUTPUT" .

cd ../..

echo "Built: $OUTPUT"
echo ""
echo "To install:"
echo "1. Upload $OUTPUT to maubot management interface"
echo "2. http://localhost:29316/_matrix/maubot"
