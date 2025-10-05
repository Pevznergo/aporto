#!/bin/bash

# Minimal deployment package creation for Vast.ai
echo "Creating minimal deployment package..."

# Create deployment directory
DEPLOY_DIR="vastai_minimal"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Copy essential files only
cp upscale_app.py server.py requirements.txt config.json run_upscale.sh start_server.sh $DEPLOY_DIR/
cp setup_vastai.sh $DEPLOY_DIR/
cp test_instance.py $DEPLOY_DIR/

# Create deployment zip
zip -r vastai_minimal.zip $DEPLOY_DIR

echo "Minimal deployment package created: vastai_minimal.zip"
echo "This package can be uploaded directly to your Vast.ai instance"