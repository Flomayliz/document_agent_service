#!/bin/bash

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    sudo groupadd docker
    sudo usermod -aG docker $USER

    echo "----------------------------------------------------------------------------------------"
    echo "You may need to log out and back in for the group changes to take effect !!!!"
    echo "----------------------------------------------------------------------------------------"
else
    echo "Docker is already installed."
fi

# Start Docker service if not running
if ! systemctl is-active --quiet docker; then
    echo "Starting Docker service..."
    sudo systemctl start docker
else
    echo "Docker service is already running."
fi



    