# GitHub Secrets Configuration

To enable Docker Hub publishing, you need to configure the following secrets in your GitHub repository:

## Required Secrets

1. **DOCKER_USERNAME**: Your Docker Hub username
2. **DOCKER_PASSWORD**: Your Docker Hub password or access token

## How to add secrets

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. In the left sidebar, click on "Secrets and variables" → "Actions"
4. Click on "New repository secret"
5. Add each secret with the corresponding name and value

## Docker Hub Access Token (Recommended)

Instead of using your Docker Hub password, it's recommended to use an access token:

1. Log in to Docker Hub
2. Go to Account Settings → Security
3. Click "New Access Token"
4. Give it a descriptive name
5. Copy the token and use it as DOCKER_PASSWORD