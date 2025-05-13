#!/bin/bash
# setup_env.sh - Environment setup script for Document Execution System

# Algorand node connection
export ALGOD_ADDRESS="https://testnet-api.algonode.cloud"
export ALGOD_TOKEN=""

# Application IDs (update after deployment)
export IDENTITY_APP_ID="FILL_IN_AFTER_DEPLOYMENT"
export AGREEMENT_APP_ID="FILL_IN_AFTER_DEPLOYMENT"

# Admin/Verifier wallet (update after deployment)
export ADMIN_PRIVATE_KEY="FILL_IN_AFTER_DEPLOYMENT"
export ADMIN_ADDRESS="FILL_IN_AFTER_DEPLOYMENT"

# DocuSign Integration (if used)
export DOCUSIGN_BASE_URL="https://demo.docusign.net/restapi/v2/accounts/YOUR_ACCOUNT_ID"
export DOCUSIGN_API_KEY="YOUR_DOCUSIGN_API_KEY"
export DOCUSIGN_AUTH_TOKEN="YOUR_DOCUSIGN_AUTH_TOKEN"

echo "Environment variables set. To use them in your current shell session, run:"
echo "source setup_env.sh"