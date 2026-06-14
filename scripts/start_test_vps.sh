#!/bin/bash
set -e

# Target paths
DEV_DIR="$HOME/.vibe-server-dev"
KEY_PATH="$DEV_DIR/test_key"
CONTAINER_NAME="vibe-vps-sim"
PORT=2222

# Ensure dev config directory exists
mkdir -p "$DEV_DIR"

# 1. Generate SSH Key Pair if not exists
if [ ! -f "$KEY_PATH" ]; then
    echo "→ Generating local test SSH key..."
    ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -N "" -q
    chmod 600 "$KEY_PATH"
    echo "✓ Generated test key: $KEY_PATH"
fi

PUB_KEY_CONTENT=$(cat "${KEY_PATH}.pub")

# 2. Create a temporary Dockerfile
TMP_DOCKERFILE_DIR=$(mktemp -d)
cat <<EOF > "$TMP_DOCKERFILE_DIR/Dockerfile"
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies (openssh, sudo, curl, system tools, nginx, node, npm)
RUN apt-get update && apt-get install -y \\
    openssh-server \\
    sudo \\
    curl \\
    procps \\
    iproute2 \\
    nginx \\
    nodejs \\
    npm \\
    && rm -rf /var/lib/apt/lists/*

# Install PM2 globally
RUN npm install -g pm2

# Configure SSH daemon
RUN mkdir /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\\s*required\\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Set root password for testing password auth
RUN echo 'root:rootpassword' | chpasswd

# Setup authorized keys
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
ARG SSH_PUB_KEY
RUN echo "\$SSH_PUB_KEY" > /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
EOF

echo "→ Building Docker image for simulated VPS..."
docker build -t ubuntu-ssh-test \
    --build-arg SSH_PUB_KEY="$PUB_KEY_CONTENT" \
    "$TMP_DOCKERFILE_DIR"

# Clean up temp dir
rm -rf "$TMP_DOCKERFILE_DIR"

# 3. Spin down existing container if running
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "→ Stopping and removing existing $CONTAINER_NAME container..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# 4. Start new container
echo "→ Launching simulated VPS container on port $PORT..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:22" \
    ubuntu-ssh-test

echo ""
echo "=========================================================="
echo "✓ Local VPS Simulator is running successfully!"
echo "=========================================================="
echo "Use the following details to register this server in vps-dev:"
echo ""
echo "1. Run: vps-dev add-server"
echo "   - Profile name: dev-vps"
echo "   - IP/Hostname: 127.0.0.1"
echo "   - Username: root"
echo "   - Port: $PORT"
echo "   - Key path: $KEY_PATH"
echo ""
echo "2. Connect to it:"
echo "   - Run: vps-dev connect dev-vps"
echo ""
echo "Alternative Password login: 'rootpassword' (master password: password)"
echo "=========================================================="
