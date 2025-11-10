#!/bin/bash
set -e

echo "Installing local development packages..."

# Install nexusql first (ia_modules depends on it)
if [ -d "/nexusql" ]; then
    echo "Installing nexusql from /nexusql..."
    pip install -e /nexusql
else
    echo "WARNING: /nexusql not found. Make sure the volume is mounted."
fi

# Install ia_modules if mounted
if [ -d "/ia_modules" ]; then
    echo "Installing ia_modules from /ia_modules..."
    pip install -e /ia_modules
else
    echo "WARNING: /ia_modules not found. Make sure the volume is mounted."
fi

# Install ia_auth_sessions if mounted
if [ -d "/ia_auth_sessions" ]; then
    echo "Installing ia_auth_sessions from /ia_auth_sessions..."
    pip install -e /ia_auth_sessions
else
    echo "WARNING: /ia_auth_sessions not found. Make sure the volume is mounted."
fi

echo "Starting uvicorn server with hot reload..."
exec uvicorn main:app --host 0.0.0.0 --port 8091 --reload
