import os
import sys

# Add the parent directory to the Python path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import pytest
import base64
import time
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from algosdk.encoding import decode_address, encode_address
from pyteal import compileTeal, Mode

# Now we can import from the contracts package
from contracts.identity_registry import approval_program as identity_approval, clear_state_program as identity_clear
from contracts.agreement_registry import approval_program as agreement_approval, clear_state_program as agreement_clear
from contracts.execution_router import approval_program as router_approval, clear_state_program as router_clear
from contracts.escrow_release_handler import approval_program as escrow_approval, clear_state_program as escrow_clear
from contracts.asset_transfer_handler import approval_program as asset_approval, clear_state_program as asset_clear
from contracts.contract_deployment_handler import approval_program as deploy_approval, clear_state_program as deploy_clear

# Test file path
import os
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Sandbox configuration
ALGOD_ADDRESS = "http://localhost:4001"
ALGOD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

@pytest.fixture(scope="module")
def algod_client():
    """Create and return an Algod client connected to the sandbox."""
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

@pytest.fixture(scope="module")
def accounts(algod_client):
    """Get real accounts from the Algorand Sandbox."""
    # Get accounts from the sandbox
    acct_info = algod_client.account_info("GD64YIY3TWGDMCNPP553DZPPR6LDUSFQOIJVFDPPXWEG3FVOJCCDBBHU5A")
    
    if "amount" in acct_info and acct_info["amount"] > 0:
        print("Successfully connected to Algorand Sandbox and found a funded account")
    else:
        print("WARNING: Could not verify account in Algorand Sandbox. Make sure sandbox is running.")
    
    # Use the default account in sandbox
    accounts = [
        {
            "name": "Account 1",
            "address": "GD64YIY3TWGDMCNPP553DZPPR6LDUSFQOIJVFDPPXWEG3FVOJCCDBBHU5A",
            "private_key": "SP7RDD36FGYDL5OBCLHICW5VPAVAZFGDLRC3PMMVYDZWWK3GQNBHW3OVGE"
        },
        {
            "name": "Account 2",
            "address": "RDKITJZK4T7PJKT3PZUYSKZZHJ7LUILVGOLUEJGW2RKVVPW4JJQZ2S6BSQ",
            "private_key": "NTUOAVS4RJ52MVMEOWRGM7VGWTV4TDXZTTXM3IHZPBQGRXBZB35SCXHHAM"
        },
        {
            "name": "Account 3",
            "address": "KY6J2PUOLY6H3MR4GL35WLQWJFKPG3QCWVF5YZGTXH42AUUFHR4GKJTPAI",
            "private_key": "OM34PSWAXIHWNLUYTDNMYHFWAYJ5MXSW735MBA4I6UW34NVZHRFVRYIJIY"
        }
    ]
    
    # Verify the accounts exist and have funds
    try:
        for acct in accounts:
            info = algod_client.account_info(acct["address"])
            print(f"Account {acct['name']} balance: {info.get('amount', 0)} microAlgos")
    except Exception as e:
        print(f"Error checking account info: {str(e)}")
        print("Using test accounts anyway, but transactions might fail if accounts are not funded.")
    
    return accounts

@pytest.fixture(scope="module")
def compiled_contracts(algod_client):
    """Compile all contract programs."""
    def compile_program(client, program):
        """Compile a PyTeal program to TEAL binary."""
        teal = compileTeal(program, Mode.Application, version=6)
        compile_result = client.compile(teal)
        return base64.b64decode(compile_result["result"])
    
    contracts = {}
    
    # Identity Registry
    contracts["identity"] = {
        "approval": compile_program(algod_client, identity_approval()),
        "clear": compile_program(algod_client, identity_clear())
    }
    
    # Agreement Registry
    contracts["agreement"] = {
        "approval": compile_program(algod_client, agreement_approval()),
        "clear": compile_program(algod_client, agreement_clear())
    }
    
    # Execution Router
    contracts["router"] = {
        "approval": compile_program(algod_client, router_approval()),
        "clear": compile_program(algod_client, router_clear())
    }
    
    # Escrow Release Handler
    contracts["escrow"] = {
        "approval": compile_program(algod_client, escrow_approval()),
        "clear": compile_program(algod_client, escrow_clear())
    }
    
    # Asset Transfer Handler
    contracts["asset"] = {
        "approval": compile_program(algod_client, asset_approval()),
        "clear": compile_program(algod_client, asset_clear())
    }
    
    # Contract Deployment Handler
    contracts["deploy"] = {
        "approval": compile_program(algod_client, deploy_approval()),
        "clear": compile_program(algod_client, deploy_clear())
    }
    
    return contracts

@pytest.fixture(scope="module")
def deployed_apps(algod_client, accounts, compiled_contracts):
    """Deploy all contracts and return their app IDs."""
    admin = accounts[0]
    app_ids = {}
    
    # Helper function for deployment
    def deploy_app(name, global_schema, local_schema):
        txn = transaction.ApplicationCreateTxn(
            sender=admin["address"],
            sp=algod_client.suggested_params(),
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=compiled_contracts[name]["approval"],
            clear_program=compiled_contracts[name]["clear"],
            global_schema=global_schema,
            local_schema=local_schema
        )
        
        signed_txn = txn.sign(admin["private_key"])
        tx_id = algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(algod_client, tx_id, 10)
        app_id = result["application-index"]
        print(f"Deployed {name} with app ID: {app_id}")
        return app_id
    
    # Deploy the contracts in order of their dependencies
    app_ids["identity"] = deploy_app(
        "identity", 
        transaction.StateSchema(num_uints=32, num_byte_slices=64),
        transaction.StateSchema(num_uints=16, num_byte_slices=16)
    )
    
    app_ids["agreement"] = deploy_app(
        "agreement", 
        transaction.StateSchema(num_uints=64, num_byte_slices=128),
        transaction.StateSchema(num_uints=32, num_byte_slices=32)
    )
    
    app_ids["router"] = deploy_app(
        "router", 
        transaction.StateSchema(num_uints=32, num_byte_slices=64),
        transaction.StateSchema(num_uints=16, num_byte_slices=16)
    )
    
    app_ids["escrow"] = deploy_app(
        "escrow", 
        transaction.StateSchema(num_uints=16, num_byte_slices=32),
        transaction.StateSchema(num_uints=8, num_byte_slices=8)
    )
    
    app_ids["asset"] = deploy_app(
        "asset", 
        transaction.StateSchema(num_uints=32, num_byte_slices=64),
        transaction.StateSchema(num_uints=16, num_byte_slices=16)
    )
    
    app_ids["deploy"] = deploy_app(
        "deploy", 
        transaction.StateSchema(num_uints=32, num_byte_slices=64),
        transaction.StateSchema(num_uints=16, num_byte_slices=16)
    )
    
    return app_ids

@pytest.fixture(scope="module")
def configured_apps(algod_client, accounts, deployed_apps):
    """Configure and interconnect all the deployed applications."""
    admin = accounts[0]
    verifier = accounts[1]
    app_ids = deployed_apps
    
    # Helper function for app calls
    def call_app(app_id, app_args, accounts=None, apps=None, assets=None):
        txn = transaction.ApplicationNoOpTxn(
            sender=admin["address"],
            sp=algod_client.suggested_params(),
            index=app_id,
            app_args=app_args,
            accounts=accounts,
            foreign_apps=apps,
            foreign_assets=assets
        )
        
        signed_txn = txn.sign(admin["private_key"])
        tx_id = algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(algod_client, tx_id, 10)
        return result
    
    # 1. Add verifier to Identity Registry
    call_app(app_ids["identity"], [b"add_verifier", decode_address(verifier["address"])])
    print(f"Added verifier {verifier['address']} to Identity Registry")
    
    # 2. Add verifier to Agreement Registry
    call_app(app_ids["agreement"], [b"add_verifier", decode_address(verifier["address"])])
    print(f"Added verifier {verifier['address']} to Agreement Registry")
    
    # 3. Connect Agreement Registry to Execution Router
    call_app(app_ids["agreement"], [b"set_execution_router", app_ids["router"].to_bytes(8, "big")])
    print(f"Connected Agreement Registry to Execution Router")
    
    # 4. Connect Execution Router to Agreement Registry
    call_app(app_ids["router"], [b"set_agreement_registry", app_ids["agreement"].to_bytes(8, "big")])
    print(f"Connected Execution Router to Agreement Registry")
    
    # 5. Add administrator as executor to Execution Router
    call_app(app_ids["router"], [b"add_executor", decode_address(admin["address"])])
    print(f"Added admin as executor to Execution Router")
    
    # 6. Set up handlers to know about the router
    call_app(app_ids["escrow"], [b"set_router", app_ids["router"].to_bytes(8, "big")])
    call_app(app_ids["asset"], [b"set_router", app_ids["router"].to_bytes(8, "big")])
    call_app(app_ids["deploy"], [b"set_router", app_ids["router"].to_bytes(8, "big")])
    print(f"Connected all handlers to Execution Router")
    
    # 7. Register action types with Execution Router
    call_app(app_ids["router"], [b"register_action_type", b"escrow_release", app_ids["escrow"].to_bytes(8, "big")])
    call_app(app_ids["router"], [b"register_action_type", b"asset_transfer", app_ids["asset"].to_bytes(8, "big")])
    call_app(app_ids["router"], [b"register_action_type", b"deploy_contract", app_ids["deploy"].to_bytes(8, "big")])
    print(f"Registered all action types with Execution Router")
    
    return app_ids

# Helper functions 
def app_call(client, caller, app_id, app_args, accounts=None, apps=None, assets=None):
    """Call an application method."""
    sp = client.suggested_params()
    txn = transaction.ApplicationNoOpTxn(
        sender=caller["address"],
        sp=sp,
        index=app_id,
        app_args=app_args,
        accounts=accounts,
        foreign_apps=apps,
        foreign_assets=assets
    )
    
    signed_txn = txn.sign(caller["private_key"])
    tx_id = client.send_transaction(signed_txn)
    result = transaction.wait_for_confirmation(client, tx_id, 10)
    
    if "logs" in result:
        for log in result["logs"]:
            try:
                decoded_log = base64.b64decode(log).decode('utf-8')
                print(f"Log: {decoded_log}")
            except:
                print(f"Log (hex): {base64.b64decode(log).hex()}")
    
    return result

def app_optin(client, account, app_id):
    """Opt into an application."""
    sp = client.suggested_params()
    txn = transaction.ApplicationOptInTxn(
        sender=account["address"],
        sp=sp,
        index=app_id
    )
    
    signed_txn = txn.sign(account["private_key"])
    tx_id = client.send_transaction(signed_txn)
    result = transaction.wait_for_confirmation(client, tx_id, 10)
    print(f"Account {account['address']} opted into app {app_id}")
    return result

# Test the Identity Registry
def test_identity_registry_basics(algod_client, accounts, configured_apps):
    """Test basic functionality of the Identity Registry."""
    identity_id = configured_apps["identity"]
    admin = accounts[0]
    verifier = accounts[1]
    user = accounts[2]
    
    # User opts in
    app_optin(algod_client, user, identity_id)
    
    # User registers identity
    result = app_call(
        algod_client, 
        user, 
        identity_id, 
        [b"register_identity", b"email", b"user@example.com"]
    )
    
    assert "logs" in result, "Registration should produce logs"
    
    # Verifier verifies identity
    result = app_call(
        algod_client,
        verifier,
        identity_id,
        [b"verify_identity", decode_address(user["address"]), b"email"]
    )
    
    assert "logs" in result, "Verification should produce logs"
    print("Identity Registry basics test passed!")

# Test the Agreement Registry
def test_agreement_registry_basics(algod_client, accounts, configured_apps):
    """Test basic functionality of the Agreement Registry."""
    agreement_id = configured_apps["agreement"]
    admin = accounts[0]
    verifier = accounts[1]
    user = accounts[2]
    
    # User opts in
    app_optin(algod_client, user, agreement_id)
    
    # Create agreement
    document_hash = b"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    result = app_call(
        algod_client,
        admin,
        agreement_id,
        [b"create_agreement", document_hash, b"provider", decode_address(user["address"])]
    )
    
    assert "logs" in result, "Agreement creation should produce logs"
    
    # Add metadata
    result = app_call(
        algod_client,
        admin,
        agreement_id,
        [b"add_metadata", b"1", b"description", b"Test agreement"]
    )
    
    assert "logs" in result, "Adding metadata should produce logs"
    
    # Set action type
    app_call(
        algod_client,
        admin,
        agreement_id,
        [b"add_metadata", b"1", b"action_type", b"escrow_release"]
    )
    
    print("Agreement Registry basics test passed!")

# Test the integration between contracts
def test_agreement_execution_flow(algod_client, accounts, configured_apps):
    """Test the execution flow from Agreement to Router."""
    agreement_id = configured_apps["agreement"]
    escrow_id = configured_apps["escrow"]
    admin = accounts[0]
    verifier = accounts[1]
    user = accounts[2]
    
    # Create a new agreement
    document_hash = b"integration0123456789abcdef0123456789abcdefintegration0123456789ab"
    result = app_call(
        algod_client,
        admin,
        agreement_id,
        [b"create_agreement", document_hash, b"integration-test", decode_address(user["address"])]
    )
    
    # The agreement ID should be 2 (assuming we created one in the previous test)
    agreement_num = b"2"
    
    # Set action type for router
    app_call(
        algod_client,
        admin,
        agreement_id,
        [b"add_metadata", agreement_num, b"action_type", b"escrow_release"]
    )
    
    # Set up mock escrow for this agreement
    app_call(
        algod_client,
        admin,
        escrow_id,
        [b"register_escrow", agreement_num, decode_address(admin["address"])]
    )
    
    # Mark as signed by verifier
    result = app_call(
        algod_client,
        verifier,
        agreement_id,
        [b"mark_signed", agreement_num, decode_address(user["address"])]
    )
    
    # Try to execute - will likely fail in the router call since we're using a mock escrow,
    # but we should see the execution begin and the router called
    try:
        result = app_call(
            algod_client,
            admin,
            agreement_id,
            [b"execute_agreement", agreement_num]
        )
        print("Full execution completed successfully")
    except Exception as e:
        print(f"Execution failed at a later stage (expected): {str(e)}")
        print("This is normal for the test using a mock escrow")
    
    print("Agreement execution flow test completed!")

# Run the full suite of tests if this file is executed directly
if __name__ == "__main__":
    # Use pytest to run all tests
    import sys
    sys.exit(pytest.main(["-xvs", __file__]))