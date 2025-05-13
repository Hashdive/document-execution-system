import requests
import time
import os
import json
from algosdk import account, mnemonic
from algosdk.v2client import algod
from document_client_sdk import DocumentExecutionClient

class DocuSignVerifier:
    """
    Verifier backend that monitors DocuSign for signatures and updates
    the on-chain agreement status accordingly.
    """
    
    def __init__(self, algod_client, identity_app_id, agreement_app_id):
        """
        Initialize the DocuSign verifier.
        
        Args:
            algod_client: An initialized Algorand client
            identity_app_id: The application ID for the Identity Registry
            agreement_app_id: The application ID for the Agreement Registry
        """
        self.document_client = DocumentExecutionClient(
            algod_client, identity_app_id, agreement_app_id
        )
        
        # DocuSign API credentials
        self.docusign_base_url = os.environ.get("DOCUSIGN_BASE_URL")
        self.docusign_api_key = os.environ.get("DOCUSIGN_API_KEY")
        self.docusign_auth_token = os.environ.get("DOCUSIGN_AUTH_TOKEN")
        
        # Verifier wallet
        self.verifier_private_key = os.environ.get("VERIFIER_PRIVATE_KEY")
        self.verifier_address = account.address_from_private_key(self.verifier_private_key)
        
        # Identity mapping cache (email -> wallet address)
        self.identity_cache = {}
        
        # Agreement tracking
        self.tracked_agreements = {}  # agreement_id -> {envelope_id, signers, etc.}
    
    def create_docusign_envelope(self, document_bytes, signers):
        """
        Create a new DocuSign envelope with the document and signers.
        
        Args:
            document_bytes: The document content as bytes
            signers: List of email addresses to sign
            
        Returns:
            envelope_id: The DocuSign envelope ID
        """
        headers = {
            'Authorization': f'Bearer {self.docusign_auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Build signer data for DocuSign API
        recipients = {
            'signers': []
        }
        
        for i, email in enumerate(signers):
            recipients['signers'].append({
                'email': email,
                'name': email.split('@')[0],  # Simple name extraction
                'recipientId': str(i + 1),
                'routingOrder': str(i + 1)
            })
        
        # Create envelope definition
        envelope_definition = {
            'emailSubject': 'Please sign this document',
            'documents': [
                {
                    'documentBase64': document_bytes.decode('utf-8'),
                    'name': 'Agreement Document',
                    'fileExtension': 'pdf',
                    'documentId': '1'
                }
            ],
            'recipients': recipients,
            'status': 'sent'
        }
        
        # Call DocuSign API
        response = requests.post(
            f'{self.docusign_base_url}/envelopes',
            headers=headers,
            data=json.dumps(envelope_definition)
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create envelope: {response.text}")
        
        envelope_id = response.json()['envelopeId']
        return envelope_id
    
    def register_agreement(self, document_bytes, provider, wallet_signers, email_signers):
        """
        Create a new agreement both on DocuSign and on-chain.
        
        Args:
            document_bytes: The document content as bytes
            provider: The provider name (e.g., "DocuSign")
            wallet_signers: List of wallet addresses required to sign
            email_signers: List of email addresses corresponding to the wallets
            
        Returns:
            agreement_id: The on-chain agreement ID
        """
        # 1. Create DocuSign envelope
        envelope_id = self.create_docusign_envelope(document_bytes, email_signers)
        
        # 2. Create on-chain agreement
        document_hash = self.document_client.hash_document(document_bytes)
        agreement_id = self.document_client.create_agreement(
            self.verifier_private_key,
            document_hash,
            provider,
            wallet_signers
        )
        
        # 3. Store mapping for tracking
        self.tracked_agreements[agreement_id] = {
            'envelope_id': envelope_id,
            'wallet_signers': wallet_signers,
            'email_signers': email_signers,
            'document_hash': document_hash,
            'signed_by': set()
        }
        
        # 4. Update identity cache
        for i in range(len(wallet_signers)):
            self.identity_cache[email_signers[i]] = wallet_signers[i]
        
        return agreement_id
    
    def check_envelope_status(self, envelope_id):
        """
        Check the status of a DocuSign envelope.
        
        Args:
            envelope_id: The DocuSign envelope ID
            
        Returns:
            dict: Envelope status information including recipients and their status
        """
        headers = {
            'Authorization': f'Bearer {self.docusign_auth_token}'
        }
        
        response = requests.get(
            f'{self.docusign_base_url}/envelopes/{envelope_id}/recipients',
            headers=headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get envelope status: {response.text}")
        
        return response.json()
    
    def update_agreement_signatures(self, agreement_id):
        """
        Check for new signatures in DocuSign and update the on-chain agreement.
        
        Args:
            agreement_id: The on-chain agreement ID
            
        Returns:
            bool: True if all signatures are complete, False otherwise
        """
        if agreement_id not in self.tracked_agreements:
            raise Exception(f"Agreement {agreement_id} not being tracked")
        
        agreement = self.tracked_agreements[agreement_id]
        envelope_id = agreement['envelope_id']
        
        # Get latest envelope status
        status = self.check_envelope_status(envelope_id)
        
        # Check for new signatures
        all_signed = True
        for signer in status['signers']:
            email = signer['email']
            signed = signer['status'] == 'completed'
            
            if signed and email not in agreement['signed_by']:
                # New signature detected
                wallet = self.identity_cache.get(email)
                if wallet:
                    # Mark as signed on-chain
                    self.document_client.mark_signed(
                        self.verifier_private_key,
                        agreement_id,
                        wallet
                    )
                    
                    # Update tracking
                    agreement['signed_by'].add(email)
                    print(f"Marked agreement {agreement_id} as signed by {email} ({wallet})")
            
            all_signed = all_signed and signed
        
        return all_signed
    
    def execute_if_complete(self, agreement_id):
        """
        Execute the agreement if all signatures are complete.
        
        Args:
            agreement_id: The on-chain agreement ID
            
        Returns:
            bool: True if executed, False otherwise
        """
        if agreement_id not in self.tracked_agreements:
            raise Exception(f"Agreement {agreement_id} not being tracked")
        
        agreement = self.tracked_agreements[agreement_id]
        
        # Check if all signed
        if len(agreement['signed_by']) == len(agreement['wallet_signers']):
            # Execute the agreement
            self.document_client.execute_agreement(
                self.verifier_private_key,
                agreement_id,
                agreement['wallet_signers']
            )
            print(f"Executed agreement {agreement_id}")
            return True
        
        return False
    
    def monitor_agreements(self, check_interval=60):
        """
        Continuously monitor all tracked agreements for new signatures.
        
        Args:
            check_interval: How often to check for updates (in seconds)
        """
        print(f"Starting DocuSign monitor, checking every {check_interval} seconds...")
        
        while True:
            for agreement_id in list(self.tracked_agreements.keys()):
                try:
                    all_signed = self.update_agreement_signatures(agreement_id)
                    
                    if all_signed:
                        executed = self.execute_if_complete(agreement_id)
                        if executed:
                            # Remove from tracking once executed
                            del self.tracked_agreements[agreement_id]
                
                except Exception as e:
                    print(f"Error processing agreement {agreement_id}: {str(e)}")
            
            time.sleep(check_interval)


class AdobeSignVerifier:
    """
    Similar implementation for Adobe Sign integration.
    This would follow the same pattern but use Adobe's API.
    """
    pass


# Example usage
def main():
    # Initialize Algorand client
    algod_address = "https://testnet-api.algonode.cloud"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)
    
    # Application IDs
    identity_app_id = int(os.environ.get("IDENTITY_APP_ID", "0"))
    agreement_app_id = int(os.environ.get("AGREEMENT_APP_ID", "0"))
    
    # Initialize verifier
    verifier = DocuSignVerifier(algod_client, identity_app_id, agreement_app_id)
    
    # Example: Create a new agreement
    document_bytes = b"This is a sample agreement between Alice and Bob."
    
    wallet_signers = [
        "ALICE_WALLET_ADDRESS",
        "BOB_WALLET_ADDRESS"
    ]
    
    email_signers = [
        "alice@example.com",
        "bob@example.com"
    ]
    
    agreement_id = verifier.register_agreement(
        document_bytes,
        "DocuSign",
        wallet_signers,
        email_signers
    )
    
    print(f"Created agreement {agreement_id}")
    
    # Start monitoring
    verifier.monitor_agreements()

if __name__ == "__main__":
    main()