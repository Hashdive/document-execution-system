# test_identity_registry.py

import base64
import json
import time
import os
import sys
import traceback
from dotenv import load_dotenv
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from algosdk.error import AlgodHTTPError

# Load environment variables from .env file
load_dotenv()

# Get deployed contract IDs
IDENTITY_APP_ID = int(os.environ.get("IDENTITY_APP_ID"))
ADMIN_PRIVATE_KEY = os.environ.get("ADMIN_PRIVATE_KEY")
ADMIN_ADDRESS = os.environ.get("ADMIN_ADDRESS")

# Setup Algorand client
algod_address = "https://testnet-api.algonode.cloud"
algod_token = ""
client = algod.AlgodClient(algod_token, algod_address)

# Helper functions
def create_test_account():
    """Create a new test account."""
    private_key, address = account.generate_account()
    mnem = mnemonic.from_private_key(private_key)
    
    print(f"Created test account: {address}")
    print(f"Mnemonic: {mnem}")
    
    return private_key, address, mnem

def fund_account(address):
    """Prompt to fund an account using the TestNet dispenser."""
    print(f"Please fund account {address} with the TestNet dispenser at:")
    print("https://bank.testnet.algorand.network/")
    input("Press Enter after funding the account...")
    
    # Verify funding
    account_info = client.account_info(address)
    balance = account_info.get('amount', 0) / 1000000
    print(f"Account balance: {balance} Algos")
    
    return balance > 0

def wait_for_confirmation(client, txid):
    """Wait for a transaction to be confirmed."""
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    
    print(f"Transaction {txid} confirmed in round {txinfo.get('confirmed-round')}.")
    return txinfo

def call_app(client, sender_private_key, app_id, app_args, accounts=None, foreign_apps=None, foreign_assets=None):
    """Call a smart contract application."""
    sender = account.address_from_private_key(sender_private_key)
    params = client.suggested_params()
    
    # Create the transaction
    txn = transaction.ApplicationNoOpTxn(
        sender=sender,
        sp=params,
        index=app_id,
        app_args=app_args,
        accounts=accounts if accounts else [],
        foreign_apps=foreign_apps if foreign_apps else [],
        foreign_assets=foreign_assets if foreign_assets else []
    )
    
    # Sign the transaction
    signed_txn = txn.sign(sender_private_key)
    
    # Submit the transaction
    tx_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation
    return wait_for_confirmation(client, tx_id)

def read_global_state(client, app_id):
    """Read the global state of an application."""
    app_info = client.application_info(app_id)
    global_state = {}
    
    for item in app_info['params']['global-state']:
        key = base64.b64decode(item['key']).decode('utf-8')
        if item['value']['type'] == 1:  # byte array
            try:
                value = base64.b64decode(item['value']['bytes']).decode('utf-8')
            except UnicodeDecodeError:
                value = base64.b64decode(item['value']['bytes']).hex()
        else:  # uint
            value = item['value']['uint']
        
        global_state[key] = value
    
    return global_state

def read_local_state(client, app_id, address):
    """Read the local state of an application for an account."""
    account_info = client.account_info(address)
    local_state = {}
    
    for app in account_info.get('apps-local-state', []):
        if app['id'] == app_id:
            for item in app.get('key-value', []):
                key = base64.b64decode(item['key']).decode('utf-8')
                if item['value']['type'] == 1:  # byte array
                    try:
                        value = base64.b64decode(item['value']['bytes']).decode('utf-8')
                    except UnicodeDecodeError:
                        value = base64.b64decode(item['value']['bytes']).hex()
                else:  # uint
                    value = item['value']['uint']
                
                local_state[key] = value
    
    return local_state

def opt_in_to_app_with_args(client, private_key, app_id):
    """Opt-in to a smart contract application with a dummy argument."""
    sender = account.address_from_private_key(private_key)
    params = client.suggested_params()
    
    # This contract seems to require application args even during opt-in
    # Adding a dummy "noop" argument for opt-in
    # This is unusual but appears to be how this contract was implemented
    
    # Create the transaction
    txn = transaction.ApplicationOptInTxn(
        sender=sender,
        sp=params,
        index=app_id,
        app_args=[b"noop"]  # Adding a dummy argument to satisfy the contract
    )
    
    # Sign the transaction
    signed_txn = txn.sign(private_key)
    
    # Submit the transaction
    tx_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation
    return wait_for_confirmation(client, tx_id)

def check_app_opted_in(client, address, app_id):
    """Check if an account has opted into an application."""
    try:
        account_info = client.account_info(address)
        for app in account_info.get('apps-local-state', []):
            if app['id'] == app_id:
                return True
        return False
    except:
        return False

def test_identity_registry():
    """Test identity registration and verification functionality."""
    print("\n=== Testing Identity Registry ===")
    
    # 1. Create test accounts
    user_private_key, user_address, _ = create_test_account()
    verifier_private_key, verifier_address, _ = create_test_account()
    
    # 2. Fund the accounts
    fund_account(user_address)
    fund_account(verifier_address)
    
    # 3. Print contract info
    try:
        app_info = client.application_info(IDENTITY_APP_ID)
        print(f"\nContract Info:")
        print(f"ID: {IDENTITY_APP_ID}")
        print(f"Creator: {app_info['params']['creator']}")
        print(f"Global State Size: {app_info['params']['global-state-schema']}")
        print(f"Local State Size: {app_info['params']['local-state-schema']}")
    except Exception as e:
        print(f"Error getting contract info: {str(e)}")
    
    # 4. Opt user into the Identity Registry with a dummy argument
    print("\nOpting user into Identity Registry...")
    if not check_app_opted_in(client, user_address, IDENTITY_APP_ID):
        try:
            opt_in_to_app_with_args(client, user_private_key, IDENTITY_APP_ID)
            print(f"User {user_address} opted into Identity Registry.")
        except Exception as e:
            print(f"Error opting user into app: {str(e)}")
            traceback.print_exc()
            return False
    else:
        print(f"User {user_address} already opted into Identity Registry.")
    
    # 5. Add a verifier to the identity registry
    print("\nAdding verifier to identity registry...")
    try:
        result = call_app(
            client,
            ADMIN_PRIVATE_KEY,
            IDENTITY_APP_ID,
            [b"add_verifier", verifier_address.encode()]
        )
        print(f"Verifier {verifier_address} added.")
    except Exception as e:
        print(f"Error adding verifier: {str(e)}")
        traceback.print_exc()
        return False
    
    # 6. Verify verifier was added
    print("\nChecking verifier status...")
    global_state = read_global_state(client, IDENTITY_APP_ID)
    verifier_key = f"verifier_{verifier_address}"
    
    verifier_added = False
    for key, value in global_state.items():
        if key == verifier_key and value == 1:
            verifier_added = True
            break
    
    if verifier_added:
        print("✅ Verifier successfully added!")
    else:
        print("❌ Verifier addition failed or not found in state.")
        # Print all global state for debugging
        print("Global state:")
        for key, value in global_state.items():
            print(f"  {key}: {value}")
    
    # 7. Register an identity claim
    print("\nRegistering identity claim...")
    claim_type = "email"
    claim_value = "test@example.com"
    
    try:
        result = call_app(
            client,
            user_private_key,
            IDENTITY_APP_ID,
            [b"register_identity", claim_type.encode(), claim_value.encode()]
        )
        print(f"Identity claim registered: {claim_type}:{claim_value}")
    except Exception as e:
        print(f"Error registering identity: {str(e)}")
        traceback.print_exc()
        return False
    
    # 8. Check if the claim was stored in local state
    local_state = read_local_state(client, IDENTITY_APP_ID, user_address)
    claim_key = f"{claim_type}_{claim_value}"
    
    if claim_key in local_state and local_state[claim_key] == 1:
        print("✅ Identity claim successfully stored!")
    else:
        print("❌ Identity claim storage failed or not found in local state.")
        print("Local state:")
        for key, value in local_state.items():
            print(f"  {key}: {value}")
        return False
    
    # 9. Opt verifier into the app with a dummy argument
    print("\nOpting verifier into Identity Registry...")
    if not check_app_opted_in(client, verifier_address, IDENTITY_APP_ID):
        try:
            opt_in_to_app_with_args(client, verifier_private_key, IDENTITY_APP_ID)
            print(f"Verifier {verifier_address} opted into Identity Registry.")
        except Exception as e:
            print(f"Error opting verifier into app: {str(e)}")
            traceback.print_exc()
            return False
    else:
        print(f"Verifier {verifier_address} already opted into Identity Registry.")
    
    # 10. Verify the identity claim
    print("\nVerifying identity claim...")
    try:
        result = call_app(
            client,
            verifier_private_key,
            IDENTITY_APP_ID,
            [b"verify_identity", user_address.encode(), claim_type.encode()]
        )
        print(f"Identity claim verification attempted.")
    except Exception as e:
        print(f"Error verifying identity: {str(e)}")
        traceback.print_exc()
        return False
    
    # 11. Read the local state to confirm verification
    print("\nReading identity verification status...")
    local_state = read_local_state(client, IDENTITY_APP_ID, user_address)
    
    # Display the verification status
    verified_key = f"{claim_type}_verified"
    if verified_key in local_state and local_state[verified_key] == 1:
        print(f"✅ Identity claim successfully verified!")
    else:
        print(f"❌ Identity verification failed or status not found!")
        print("Local state:")
        for key, value in local_state.items():
            print(f"  {key}: {value}")
        return False
    
    # 12. Test updating a claim
    print("\nUpdating identity claim...")
    new_claim_value = "new@example.com"
    
    try:
        result = call_app(
            client,
            user_private_key,
            IDENTITY_APP_ID,
            [b"update_claim", claim_type.encode(), claim_value.encode(), new_claim_value.encode()]
        )
        print(f"Identity claim update attempted: {claim_type}:{claim_value} -> {new_claim_value}")
    except Exception as e:
        print(f"Error updating identity claim: {str(e)}")
        traceback.print_exc()
        return False
    
    # 13. Verify the claim has changed and status reset
    local_state = read_local_state(client, IDENTITY_APP_ID, user_address)
    new_claim_key = f"{claim_type}_{new_claim_value}"
    old_claim_key = f"{claim_type}_{claim_value}"
    verified_key = f"{claim_type}_verified"
    
    claim_updated = new_claim_key in local_state and local_state[new_claim_key] == 1
    old_claim_removed = old_claim_key not in local_state
    verification_reset = verified_key in local_state and local_state[verified_key] == 0
    
    if claim_updated and old_claim_removed and verification_reset:
        print(f"✅ Identity claim successfully updated and verification reset!")
    else:
        print(f"❌ Identity claim update verification failed!")
        print("Local state:")
        for key, value in local_state.items():
            print(f"  {key}: {value}")
        return False
    
    print("\n✅ Identity Registry Test Completed Successfully!")
    return True

if __name__ == "__main__":
    print("Starting Identity Registry Test...")
    try:
        print(f"Connected to Algorand TestNet. Current round: {client.status()['last-round']}")
        print(f"Using admin account: {ADMIN_ADDRESS}")
        print(f"Testing Identity Registry with App ID: {IDENTITY_APP_ID}")
        
        # Run the test
        success = test_identity_registry()
        
        if success:
            print("\n🎉 Identity Registry Test PASSED!")
        else:
            print("\n❌ Identity Registry Test FAILED!")
        
    except Exception as e:
        print(f"Error during test execution: {str(e)}")
        traceback.print_exc()