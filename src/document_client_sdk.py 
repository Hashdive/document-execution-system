from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.encoding import encode_address, decode_address
import base64
import hashlib

class DocumentExecutionClient:
    """
    Client SDK for interacting with the Document Execution Smart Contract System.
    """
    
    def __init__(self, algod_client, identity_app_id, agreement_app_id):
        """
        Initialize the client with the necessary application IDs and Algorand client.
        
        Args:
            algod_client: An initialized Algorand client
            identity_app_id: The application ID for the Identity Registry
            agreement_app_id: The application ID for the Agreement Registry
        """
        self.algod_client = algod_client
        self.identity_app_id = identity_app_id
        self.agreement_app_id = agreement_app_id
    
    # ===== Identity Registry Functions =====
    
    def register_identity(self, private_key, claim_type, claim_value):
        """
        Register an identity claim (e.g., email, DID) for a wallet.
        
        Args:
            private_key: The private key of the wallet to register
            claim_type: The type of identity claim (e.g., "email", "DID")
            claim_value: The value of the identity claim (e.g., "alice@example.com")
        """
        sender = account.address_from_private_key(private_key)
        
        # Create application call transaction
        params = self.algod_client.suggested_params()
        txn = transaction.ApplicationCallTxn(
            sender=sender,
            sp=params,
            index=self.identity_app_id,
            app_args=["register_identity", claim_type, claim_value],
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Sign and send transaction
        signed_txn = txn.sign(private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        self._wait_for_confirmation(tx_id)
        
        return tx_id
    
    def verify_identity(self, verifier_private_key, wallet_to_verify, claim_type):
        """
        Verify an identity claim for a wallet (only callable by verifiers).
        
        Args:
            verifier_private_key: The private key of the verifier
            wallet_to_verify: The address of the wallet to verify
            claim_type: The type of identity claim to verify
        """
        verifier = account.address_from_private_key(verifier_private_key)
        
        # Create application call transaction
        params = self.algod_client.suggested_params()
        txn = transaction.ApplicationCallTxn(
            sender=verifier,
            sp=params,
            index=self.identity_app_id,
            app_args=["verify_identity", wallet_to_verify, claim_type],
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Sign and send transaction
        signed_txn = txn.sign(verifier_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        self._wait_for_confirmation(tx_id)
        
        return tx_id
    
    def add_verifier(self, admin_private_key, verifier_address):
        """
        Add a new verifier to the system (admin only).
        
        Args:
            admin_private_key: The private key of the admin
            verifier_address: The address to add as a verifier
        """
        admin = account.address_from_private_key(admin_private_key)
        
        # Add to Identity Registry
        params = self.algod_client.suggested_params()
        txn1 = transaction.ApplicationCallTxn(
            sender=admin,
            sp=params,
            index=self.identity_app_id,
            app_args=["add_verifier", verifier_address],
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Add to Agreement Registry
        params = self.algod_client.suggested_params()
        txn2 = transaction.ApplicationCallTxn(
            sender=admin,
            sp=params,
            index=self.agreement_app_id,
            app_args=["add_verifier", verifier_address],
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Group transactions
        gid = transaction.calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid
        
        # Sign and send transactions
        signed_txn1 = txn1.sign(admin_private_key)
        signed_txn2 = txn2.sign(admin_private_key)
        
        signed_group = [signed_txn1, signed_txn2]
        tx_id = self.algod_client.send_transactions(signed_group)
        
        # Wait for confirmation
        self._wait_for_confirmation(tx_id)
        
        return tx_id
    
    # ===== Agreement Registry Functions =====
    
    def create_agreement(self, creator_private_key, document_hash, provider, signers):
        """
        Create a new agreement with document hash, provider, and list of required signers.
        
        Args:
            creator_private_key: The private key of the agreement creator
            document_hash: The SHA-256 hash of the document (bytes32)
            provider: The document provider (e.g., "DocuSign")
            signers: List of wallet addresses that need to sign
        """
        creator = account.address_from_private_key(creator_private_key)
        
        # If document_hash is a string, convert to bytes
        if isinstance(document_hash, str):
            if document_hash.startswith("0x"):
                document_hash = bytes.fromhex(document_hash[2:])
            else:
                document_hash = bytes.fromhex(document_hash)
        
        # Create application call transaction
        params = self.algod_client.suggested_params()
        
        # Convert signers to application arguments
        app_args = ["create_agreement", document_hash, provider]
        app_args.extend(signers)
        
        txn = transaction.ApplicationCallTxn(
            sender=creator,
            sp=params,
            index=self.agreement_app_id,
            app_args=app_args,
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Sign and send transaction
        signed_txn = txn.sign(creator_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        self._wait_for_confirmation(tx_id)
        
        # Get the agreement ID from the transaction result
        # Note: In a real implementation, you would parse this from transaction logs
        # For now, we'll assume it returns the latest agreement ID
        agreement_id = self._get_latest_agreement_id()
        
        return agreement_id
    
    def mark_signed(self, verifier_private_key, agreement_id, signer_wallet):
        """
        Mark an agreement as signed by a specific wallet (only callable by verifiers).
        
        Args:
            verifier_private_key: The private key of the verifier
            agreement_id: The ID of the agreement
            signer_wallet: The address of the signer
        """
        verifier = account.address_from_private_key(verifier_private_key)
        
        # Create application call transaction
        params = self.algod_client.suggested_params()
        txn = transaction.ApplicationCallTxn(
            sender=verifier,
            sp=params,
            index=self.agreement_app_id,
            app_args=["mark_signed", agreement_id, signer_wallet],
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Sign and send transaction
        signed_txn = txn.sign(verifier_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        self._wait_for_confirmation(tx_id)
        
        return tx_id
    
    def execute_agreement(self, executor_private_key, agreement_id, signers):
        """
        Execute an agreement if all signers have signed.
        
        Args:
            executor_private_key: The private key of the executor
            agreement_id: The ID of the agreement
            signers: List of all signers for the agreement
        """
        executor = account.address_from_private_key(executor_private_key)
        
        # Create application call transaction
        params = self.algod_client.suggested_params()
        
        # Convert agreement_id and signers to application arguments
        app_args = ["execute_agreement", str(agreement_id)]
        app_args.extend(signers)
        
        txn = transaction.ApplicationCallTxn(
            sender=executor,
            sp=params,
            index=self.agreement_app_id,
            app_args=app_args,
            on_complete=transaction.OnComplete.NoOpOC
        )
        
        # Sign and send transaction
        signed_txn = txn.sign(executor_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        self._wait_for_confirmation(tx_id)
        
        return tx_id
    
    # ===== Utility Functions =====
    
    def hash_document(self, document_bytes):
        """
        Create a SHA-256 hash of a document.
        
        Args:
            document_bytes: The document as bytes
        
        Returns:
            bytes32: The SHA-256 hash of the document
        """
        return hashlib.sha256(document_bytes).digest()
    
    def _wait_for_confirmation(self, txid):
        """
        Wait until the transaction is confirmed or rejected.
        """
        last_round = self.algod_client.status().get('last-round')
        txinfo = self.algod_client.pending_transaction_info(txid)
        
        while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
            print("Waiting for confirmation...")
            last_round += 1
            self.algod_client.status_after_block(last_round)
            txinfo = self.algod_client.pending_transaction_info(txid)
        
        print(f"Transaction {txid} confirmed in round {txinfo.get('confirmed-round')}.")
        return txinfo
    
    def _get_latest_agreement_id(self):
        """
        Get the latest agreement ID from the global state.
        
        In a real implementation, this would parse application state.
        """
        # This is a simplification - in a real app, you'd query the app's global state
        app_info = self.algod_client.application_info(self.agreement_app_id)
        state = app_info['params']['global-state']
        
        # Find the counter value
        for item in state:
            if base64.b64decode(item['key']) == b'agreement_counter':
                # The counter is the next ID, so we want the previous value
                return base64.b64decode(item['value']['bytes']) - 1
        
        return 0

# Example usage
def example_usage():
    # Initialize Algorand client
    algod_address = "https://testnet-api.algonode.cloud"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)
    
    # Example application IDs (would be obtained after deploying the smart contracts)
    identity_app_id = 12345
    agreement_app_id = 67890
    
    # Initialize the client
    client = DocumentExecutionClient(algod_client, identity_app_id, agreement_app_id)
    
    # Example: Generate test accounts
    private_key1, address1 = account.generate_account()
    private_key2, address2 = account.generate_account()
    admin_private_key, admin_address = account.generate_account()
    verifier_private_key, verifier_address = account.generate_account()
    
    # Example: Register identities
    client.register_identity(private_key1, "email", "alice@example.com")
    client.register_identity(private_key2, "email", "bob@example.com")
    
    # Example: Add verifier
    client.add_verifier(admin_private_key, verifier_address)
    
    # Example: Verify identities
    client.verify_identity(verifier_private_key, address1, "email")
    client.verify_identity(verifier_private_key, address2, "email")
    
    # Example: Create agreement
    document = b"This is a sample agreement between Alice and Bob."
    document_hash = client.hash_document(document)
    agreement_id = client.create_agreement(
        admin_private_key,
        document_hash,
        "DocuSign",
        [address1, address2]
    )
    
    # Example: Mark as signed
    client.mark_signed(verifier_private_key, agreement_id, address1)
    client.mark_signed(verifier_private_key, agreement_id, address2)
    
    # Example: Execute agreement
    client.execute_agreement(admin_private_key, agreement_id, [address1, address2])
    
    print(f"Agreement {agreement_id} successfully executed!")

if __name__ == "__main__":
    example_usage()