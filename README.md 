# Document Execution Smart Contract System

This system enables legally meaningful off-chain document signing (via DocuSign, AdobeSign, etc.) to trigger on-chain execution logic by anchoring real-world identities to blockchain wallets on Algorand.

## Features

- **Identity Anchoring**: Associate real-world identities (email, DID, orgID) with blockchain wallets
- **Multi-provider Support**: Works with DocuSign, AdobeSign, and other signing platforms
- **Flexible Identity Types**: Supports email, DID, organizational IDs, and other identity formats
- **Trust Minimization**: Path to progressive decentralization via zero-knowledge proofs
- **Legal Auditability**: Anchors document hashes and execution state on-chain

## System Architecture

The implementation consists of two primary Algorand smart contracts:

1. **Identity Registry**: Maps wallet addresses to identity claims
2. **Agreement Registry**: Stores document hashes, signer lists, and execution state

These are supported by:
- **Box Storage**: For flexible storage of agreement data
- **Off-chain Verifier**: Bridges document signing platforms to blockchain
- **Client SDK**: Enables easy integration with the system

## Repository Structure

```
├── identity_registry.py       # Identity Registry Smart Contract
├── agreement_registry.py      # Agreement Registry Smart Contract
├── document_client_sdk.py     # Client SDK for interacting with the system
├── docusign_verifier.py       # DocuSign integration backend
├── deploy_contracts.py        # Deployment script for smart contracts
├── client_application.py      # Example client application
└── README.md                  # This file
```

## Setup and Deployment

### Prerequisites

- Python 3.8+
- `py-algorand-sdk`
- `pyteal`
- Algorand node access (MainNet, TestNet, or private network)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/document-execution-system.git
   cd document-execution-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   # Algorand node connection
   export ALGOD_ADDRESS="https://testnet-api.algonode.cloud"
   export ALGOD_TOKEN=""
   
   # For DocuSign integration (if used)
   export DOCUSIGN_BASE_URL="https://demo.docusign.net/restapi/v2/accounts/YOUR_ACCOUNT_ID"
   export DOCUSIGN_API_KEY="YOUR_DOCUSIGN_API_KEY"
   export DOCUSIGN_AUTH_TOKEN="YOUR_DOCUSIGN_AUTH_TOKEN"
   
   # Admin/Verifier wallet (after deployment)
   export ADMIN_PRIVATE_KEY="YOUR_ADMIN_PRIVATE_KEY"
   export ADMIN_ADDRESS="YOUR_ADMIN_ADDRESS"
   ```

### Deployment

1. Deploy the smart contracts:
   ```
   python deploy_contracts.py
   ```
   The script will:
   - Generate a new account if needed
   - Provide instructions to fund the account via the testnet dispenser
   - Deploy both smart contracts
   - Output the application IDs needed for configuration

2. Set the application IDs as environment variables:
   ```bash
   export IDENTITY_APP_ID=12345  # Use the actual ID from deployment
   export AGREEMENT_APP_ID=67890  # Use the actual ID from deployment
   ```

## Usage

### Running the Demo

The client application provides a complete demonstration of the system:

```
python client_application.py
```

This demonstrates:
1. Identity registration
2. Agreement creation
3. Manual signing process
4. Automated integration with DocuSign

### Integration into Your Project

To integrate the Document Execution System into your own project:

1. Import the client SDK:
   ```python
   from document_client_sdk import DocumentExecutionClient
   ```

2. Initialize the client:
   ```python
   from algosdk.v2client import algod
   
   algod_client = algod.AlgodClient(algod_token, algod_address)
   document_client = DocumentExecutionClient(
       algod_client, 
       identity_app_id, 
       agreement_app_id
   )
   ```

3. Use the client to interact with the system:
   ```python
   # Register identities
   document_client.register_identity(private_key, "email", "user@example.com")
   
   # Create agreements
   document_hash = document_client.hash_document(document_bytes)
   agreement_id = document_client.create_agreement(
       private_key, 
       document_hash, 
       "DocuSign", 
       [wallet1, wallet2]
   )
   
   # Mark as signed
   document_client.mark_signed(verifier_key, agreement_id, wallet1)
   
   # Execute agreement
   document_client.execute_agreement(
       private_key, 
       agreement_id, 
       [wallet1, wallet2]
   )
   ```

### Setting Up the Verifier Backend

For automated integration with document providers:

1. Configure environment variables for the document provider API

2. Run the verifier in monitoring mode:
   ```python
   from docusign_verifier import DocuSignVerifier
   
   verifier = DocuSignVerifier(algod_client, identity_app_id, agreement_app_id)
   verifier.monitor_agreements()
   ```

## Future Enhancements

- **Zero-Knowledge Integration**: Replace the trusted verifier with ZK proofs for identity and signature verification
- **Multi-Provider Framework**: Plug-in architecture for different document providers
- **Post-Execution Actions**: Integrate with other contracts for funds release, NFT minting, etc.
- **More Identity Types**: Add support for DIDs, Verifiable Credentials, and other identity standards

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.