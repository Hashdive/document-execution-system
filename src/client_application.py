import os
import base64
import sys
from algosdk import account, mnemonic
from algosdk.v2client import algod

# Add parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import from src directory
from src.document_client_sdk import DocumentExecutionClient
from src.docusign_verifier import DocuSignVerifier

"""
Example Client Application for Document Execution System

This script demonstrates a complete workflow using the Document Execution System:
1. Register identity claims (emails linked to wallets)
2. Verify identity claims
3. Create an agreement that requires signatures
4. Monitor for signatures and execute the agreement

For a real application, each of these steps would typically be separate routes/endpoints.
"""

# Configuration - would typically be in environment variables
ALGOD_ADDRESS = os.environ.get("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.environ.get("ALGOD_TOKEN", "")
IDENTITY_APP_ID = int(os.environ.get("IDENTITY_APP_ID", "12345"))
AGREEMENT_APP_ID = int(os.environ.get("AGREEMENT_APP_ID", "67890"))

def generate_test_accounts(count=3):
    """Generate test accounts for demonstration."""
    accounts = []
    for i in range(count):
        private_key, address = account.generate_account()
        accounts.append({
            'private_key': private_key,
            'address': address,
            'email': f"user{i+1}@example.com"
        })
    return accounts

def fund_accounts(client, accounts):
    """
    Fund test accounts (for testnet, this would require manual action).
    """
    for acc in accounts:
        print(f"Fund account {acc['address']} with Algos using the testnet dispenser:")
        print("https://bank.testnet.algorand.network/")
    
    input("Press Enter after funding accounts to continue...")

def demo_identity_registration(client, admin, users):
    """
    Demonstrate identity registration and verification.
    """
    print("\n--- Identity Registration Demo ---")
    
    # Initialize the client
    doc_client = DocumentExecutionClient(client, IDENTITY_APP_ID, AGREEMENT_APP_ID)
    
    # Add admin as verifier
    try:
        doc_client.add_verifier(
            admin['private_key'],
            admin['address']
        )
        print(f"Added {admin['address']} as verifier")
    except Exception as e:
        print(f"Error adding verifier: {str(e)}")
    
    # Register identities for users
    for user in users:
        try:
            doc_client.register_identity(
                user['private_key'],
                "email",
                user['email']
            )
            print(f"Registered email '{user['email']}' for wallet {user['address']}")
        except Exception as e:
            print(f"Error registering identity: {str(e)}")
    
    # Verify identities (by admin/verifier)
    for user in users:
        try:
            doc_client.verify_identity(
                admin['private_key'],
                user['address'],
                "email"
            )
            print(f"Verified email claim for {user['address']}")
        except Exception as e:
            print(f"Error verifying identity: {str(e)}")
    
    return doc_client

def demo_agreement_creation(doc_client, admin, users):
    """
    Demonstrate agreement creation.
    """
    print("\n--- Agreement Creation Demo ---")
    
    # Create a sample document
    document_text = """
    SAMPLE AGREEMENT
    
    This agreement is made between the undersigned parties.
    
    Terms and Conditions:
    1. All parties agree to collaborate on the project.
    2. Compensation will be distributed equally.
    3. Intellectual property will be jointly owned.
    
    Signatures:
    """
    
    document_bytes = document_text.encode('utf-8')
    document_hash = doc_client.hash_document(document_bytes)
    
    # Get wallet addresses for signers
    signer_addresses = [user['address'] for user in users]
    
    # Create agreement
    try:
        agreement_id = doc_client.create_agreement(
            admin['private_key'],
            document_hash,
            "DocuSign",
            signer_addresses
        )
        print(f"Created agreement with ID: {agreement_id}")
        print(f"Document hash: {base64.b64encode(document_hash).decode('utf-8')}")
        print(f"Required signers: {', '.join(signer_addresses)}")
    except Exception as e:
        print(f"Error creating agreement: {str(e)}")
        return None
    
    return agreement_id, document_bytes

def demo_manual_signing(doc_client, admin, users, agreement_id):
    """
    Demonstrate manual signing process.
    """
    print("\n--- Manual Signing Demo ---")
    print("In a real application, DocuSign/AdobeSign would notify signers.")
    print("For this demo, we'll simulate signing via the verifier.")
    
    # Simulate signers completing their signatures
    for i, user in enumerate(users):
        input(f"Press Enter to simulate {user['email']} signing the document...")
        
        try:
            # Verifier marks the signature as complete
            doc_client.mark_signed(
                admin['private_key'],  # Verifier private key
                agreement_id,
                user['address']
            )
            print(f"Marked agreement {agreement_id} as signed by {user['address']}")
        except Exception as e:
            print(f"Error marking as signed: {str(e)}")
    
    print("\nAll signers have completed their signatures!")
    
    # Execute the agreement
    try:
        signer_addresses = [user['address'] for user in users]
        doc_client.execute_agreement(
            admin['private_key'],
            agreement_id,
            signer_addresses
        )
        print(f"Successfully executed agreement {agreement_id}!")
    except Exception as e:
        print(f"Error executing agreement: {str(e)}")

def demo_automated_workflow(client, admin, users):
    """
    Demonstrate automated DocuSign integration workflow.
    """
    print("\n--- Automated DocuSign Integration Demo ---")
    print("Note: This would require actual DocuSign API credentials.")
    print("For demo purposes, we're showing the integration pattern.")
    
    # Initialize the verifier
    verifier = DocuSignVerifier(client, IDENTITY_APP_ID, AGREEMENT_APP_ID)
    
    # Create a sample document
    document_text = """
    AUTOMATED AGREEMENT
    
    This agreement is processed through DocuSign integration.
    
    Terms and Conditions:
    1. All parties agree to the automated workflow.
    2. This demonstrates the end-to-end process.
    
    Signatures:
    """
    
    document_bytes = document_text.encode('utf-8')
    
    # Get wallet addresses and emails for signers
    wallet_signers = [user['address'] for user in users]
    email_signers = [user['email'] for user in users]
    
    print("\nCreating agreement on DocuSign and registering on-chain...")
    print("(Note: This would actually create a DocuSign envelope in a real implementation)")
    
    # Register the agreement
    try:
        agreement_id = verifier.register_agreement(
            document_bytes,
            "DocuSign",
            wallet_signers,
            email_signers
        )
        print(f"Created integrated agreement with ID: {agreement_id}")
    except Exception as e:
        print(f"This part requires actual DocuSign credentials. Error: {str(e)}")
        print("In a real implementation, the verifier would:")
        print("1. Create the DocuSign envelope")
        print("2. Register the agreement on-chain")
        print("3. Monitor DocuSign for signature completion")
        print("4. Automatically execute the agreement when all signatures are complete")
    
    print("\nTo implement the complete automated workflow:")
    print("1. Configure DocuSign API credentials in environment variables")
    print("2. Run the DocuSignVerifier in monitoring mode")
    print("3. Complete the signatures through DocuSign")
    print("4. The verifier will automatically execute the agreement")

def main():
    # Connect to Algorand client
    client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
    
    # Generate test accounts
    print("Generating test accounts...")
    admin = {
        'private_key': os.environ.get("ADMIN_PRIVATE_KEY", ""),
        'address': os.environ.get("ADMIN_ADDRESS", ""),
        'email': "admin@example.com"
    }
    
    # If admin keys aren't provided, generate them
    if not admin['private_key'] or not admin['address']:
        admin['private_key'], admin['address'] = account.generate_account()
        print(f"Generated admin account: {admin['address']}")
        print(f"Admin private key: {admin['private_key']}")
    
    users = generate_test_accounts(2)
    print(f"Generated user accounts:")
    for i, user in enumerate(users):
        print(f"User {i+1}: {user['address']} ({user['email']})")
    
    # Fund accounts (for testnet)
    fund_accounts(client, [admin] + users)
    
    # Demo: Identity Registration
    doc_client = demo_identity_registration(client, admin, users)
    
    # Demo: Agreement Creation
    agreement_data = demo_agreement_creation(doc_client, admin, users)
    if agreement_data:
        agreement_id, document_bytes = agreement_data
        
        # Demo: Manual Signing Process
        demo_manual_signing(doc_client, admin, users, agreement_id)
    
    # Demo: Automated Workflow with DocuSign
    demo_automated_workflow(client, admin, users)
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()