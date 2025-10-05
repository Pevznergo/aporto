#!/bin/bash

# Package script for Vast.ai deployment
echo "Packaging application for Vast.ai deployment..."

# Create deployment directory
DEPLOY_DIR="vastai_deployment"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Copy necessary files
cp -r upscale_app.py server.py requirements.txt config.json run_upscale.sh start_server.sh setup_vastai.sh $DEPLOY_DIR/
cp -r README.md README_UPSCALE.md README_API.md VASTAI_DEPLOYMENT.md VASTAI_API_GUIDE.md DEPLOYMENT_EXAMPLE.md $DEPLOY_DIR/
cp -r deploy_vastai.py test_deployed_api.py $DEPLOY_DIR/
cp -r vastai_direct_config.json $DEPLOY_DIR/

# Create a simple start script for the packaged version
cat > $DEPLOY_DIR/start.sh << 'EOF'
#!/bin/bash
cd /workspace
./setup_vastai.sh
./start_server.sh
EOF

chmod +x $DEPLOY_DIR/start.sh

# Create zip package
zip -r vastai_deployment.zip $DEPLOY_DIR

echo "Deployment package created: vastai_deployment.zip"
echo "You can now upload this package to your Vast.ai instance"