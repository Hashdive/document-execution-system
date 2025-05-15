import base64
import os
import sys
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from pyteal import compileTeal, Mode

# Add parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import all contract modules
from contracts.identity_registry import approval_program as identity_approval
from contracts.identity_registry import clear_state_program as identity_clear_state
from contracts.agreement_registry import approval_program as agreement_approval
from contracts.agreement_registry import clear_state_program as agreement_clear_state
from contracts.execution_router import approval_program as router_approval
from contracts.execution_router import clear_state_program as router_clear_state
from contracts.escrow_release_handler import approval_program as escrow_approval
from contracts.escrow_release_handler import clear_state_program as escrow_clear_state
from contracts.asset_transfer_handler import approval_program as asset_approval
from contracts.asset_transfer_handler import clear_state_program as asset_clear_state
from contracts.contract_deployment_handler import approval_program as deploy_approval
from contracts.contract_deployment_handler import clear_state_program as deploy_clear_state

def deploy_contracts(creator_private_key):
    """
    Deploy all smart contracts to Algorand TestNet and configure them.
    
    Args:
        creator_private_key: The private key of the creator account
    
    Returns:
        dict: App IDs of all deployed contracts
    """
    # Connect to Algorand client
    algod_address = os.environ.get("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
    algod_token = os.environ.get("ALGOD_TOKEN", "")
    client = algod.AlgodClient(algod_token, algod_address)
    
    # Get creator account info
    creator_address = account.address_from_private_key(creator_private_key)
    print(f"Deploying contracts using account: {creator_address}")
    print(f"Using Algorand node: {algod_address}")
    
    # Dictionary to store all app IDs
    app_ids = {}
    
    # 1. Deploy Identity Registry
    print("\n--- Deploying Identity Registry ---")
    app_ids["identity"] = _deploy_app(
        client, 
        creator_private_key,
        identity_approval(), 
        identity_clear_state(),
        "Identity Registry",
        global_schema=transaction.StateSchema(num_uints=16, num_byte_slices=32),
        local_schema=transaction.StateSchema(num_uints=8, num_byte_slices=8)
    )
    
    # 2. Deploy Agreement Registry - With reduced global schema to fit within Algorand limits
    print("\n--- Deploying Agreement Registry ---")
    app_ids["agreement"] = _deploy_app(
        client, 
        creator_private_key,
        agreement_approval(), 
        agreement_clear_state(),
        "Agreement Registry",
        global_schema=transaction.StateSchema(num_uints=16, num_byte_slices=48),  # Reduced from 32/64 to 16/48
        local_schema=transaction.StateSchema(num_uints=8, num_byte_slices=8),
        extra_pages=1  # Keep extra page for the large contract
    )
    
    # 3. Deploy Execution Router
    print("\n--- Deploying Execution Router ---")
    app_ids["router"] = _deploy_app(
        client, 
        creator_private_key,
        router_approval(), 
        router_clear_state(),
        "Execution Router",
        global_schema=transaction.StateSchema(num_uints=16, num_byte_slices=32),
        local_schema=transaction.StateSchema(num_uints=8, num_byte_slices=8)
    )
    
    # 4. Deploy Escrow Release Handler
    print("\n--- Deploying Escrow Release Handler ---")
    app_ids["escrow"] = _deploy_app(
        client, 
        creator_private_key,
        escrow_approval(), 
        escrow_clear_state(),
        "Escrow Release Handler",
        global_schema=transaction.StateSchema(num_uints=8, num_byte_slices=16),
        local_schema=transaction.StateSchema(num_uints=4, num_byte_slices=4)
    )
    
    # 5. Deploy Asset Transfer Handler
    print("\n--- Deploying Asset Transfer Handler ---")
    app_ids["asset"] = _deploy_app(
        client, 
        creator_private_key,
        asset_approval(), 
        asset_clear_state(),
        "Asset Transfer Handler",
        global_schema=transaction.StateSchema(num_uints=16, num_byte_slices=32),
        local_schema=transaction.StateSchema(num_uints=8, num_byte_slices=8)
    )
    
    # 6. Deploy Contract Deployment Handler
    print("\n--- Deploying Contract Deployment Handler ---")
    app_ids["deploy"] = _deploy_app(
        client, 
        creator_private_key,
        deploy_approval(), 
        deploy_clear_state(),
        "Contract Deployment Handler",
        global_schema=transaction.StateSchema(num_uints=16, num_byte_slices=32),
        local_schema=transaction.StateSchema(num_uints=8, num_byte_slices=8)
    )
    
    # Configure the contracts
    print("\n--- Configuring Contracts ---")
    
    # 7. Connect Agreement Registry to Execution Router
    print("Connecting Agreement Registry to Execution Router...")
    _call_app(
        client,
        creator_private_key,
        app_ids["agreement"],
        [b"set_execution_router", app_ids["router"].to_bytes(8, "big")]
    )
    
    # 8. Connect Execution Router to Agreement Registry
    print("Connecting Execution Router to Agreement Registry...")
    _call_app(
        client,
        creator_private_key,
        app_ids["router"],
        [b"set_agreement_registry", app_ids["agreement"].to_bytes(8, "big")]
    )
    
    # 9. Add creator as executor to Execution Router
    print("Adding creator as executor to Execution Router...")
    _call_app(
        client,
        creator_private_key,
        app_ids["router"],
        [b"add_executor", account.address_from_private_key(creator_private_key).encode()]
    )
    
    # 10. Set up handlers to know about the router
    print("Connecting handlers to Execution Router...")
    
    _call_app(
        client,
        creator_private_key,
        app_ids["escrow"],
        [b"set_router", app_ids["router"].to_bytes(8, "big")]
    )
    
    _call_app(
        client,
        creator_private_key,
        app_ids["asset"],
        [b"set_router", app_ids["router"].to_bytes(8, "big")]
    )
    
    _call_app(
        client,
        creator_private_key,
        app_ids["deploy"],
        [b"set_router", app_ids["router"].to_bytes(8, "big")]
    )
    
    # 11. Register action types with Execution Router
    print("Registering action types with Execution Router...")
    
    _call_app(
        client,
        creator_private_key,
        app_ids["router"],
        [b"register_action_type", b"escrow_release", app_ids["escrow"].to_bytes(8, "big")]
    )
    
    _call_app(
        client,
        creator_private_key,
        app_ids["router"],
        [b"register_action_type", b"asset_transfer", app_ids["asset"].to_bytes(8, "big")]
    )
    
    _call_app(
        client,
        creator_private_key,
        app_ids["router"],
        [b"register_action_type", b"deploy_contract", app_ids["deploy"].to_bytes(8, "big")]
    )
    
    print("\nAll contracts deployed and configured successfully!")
    
    return app_ids

def _deploy_app(client, creator_private_key, approval_program_func, clear_program_func, 
               app_name, global_schema, local_schema, extra_pages=0):
    """
    Deploy a single application with automatic extra page detection.
    """
    # Compile TEAL programs
    approval_teal = compileTeal(approval_program_func, mode=Mode.Application, version=6)
    clear_state_teal = compileTeal(clear_program_func, mode=Mode.Application, version=6)
    
    # Compile TEAL to bytecode
    approval_bytecode = _compile_program(client, approval_teal)
    clear_state_bytecode = _compile_program(client, clear_state_teal)
    
    # Check approval program size and automatically determine if extra pages are needed
    approval_size = len(approval_bytecode)
    print(f"Approval program size: {approval_size} bytes")
    
    # Print total global schema keys for debugging
    total_schema_keys = global_schema.num_uints + global_schema.num_byte_slices
    print(f"Total global schema keys: {total_schema_keys} (Max allowed: 64)")
    
    # If extra_pages is 0 (default) and program exceeds 2048 bytes, calculate needed pages
    if extra_pages == 0 and approval_size > 2048:
        # Calculate needed extra pages: divide by 2048 and round up
        extra_pages = (approval_size - 1) // 2048
        print(f"Program size exceeds 2048 bytes, using {extra_pages} extra pages")
    
    # Create application
    app_id = _create_app(
        client,
        creator_private_key,
        approval_bytecode,
        clear_state_bytecode,
        global_schema,
        local_schema,
        extra_pages=extra_pages
    )
    
    print(f"{app_name} deployed with app ID: {app_id}")
    return app_id

def _compile_program(client, teal_source):
    """Compile TEAL source to bytecode."""
    compile_response = client.compile(teal_source)
    return base64.b64decode(compile_response['result'])

def _create_app(client, creator_private_key, approval_program, clear_program, 
               global_schema, local_schema, extra_pages=0):
    """Create a new application with support for extra program pages."""
    # Get suggested parameters
    params = client.suggested_params()
    
    # Create the transaction
    txn = transaction.ApplicationCreateTxn(
        sender=account.address_from_private_key(creator_private_key),
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=global_schema,
        local_schema=local_schema,
        extra_pages=extra_pages  # Add support for extra pages for larger contracts
    )
    
    # Sign the transaction
    signed_txn = txn.sign(creator_private_key)
    
    # Submit the transaction
    tx_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation
    _wait_for_confirmation(client, tx_id)
    
    # Get the transaction response
    transaction_response = client.pending_transaction_info(tx_id)
    
    # Return the app ID
    return transaction_response['application-index']

def _call_app(client, private_key, app_id, app_args, accounts=None, foreign_apps=None, foreign_assets=None):
    """Call an application."""
    # Get suggested parameters
    params = client.suggested_params()
    
    # Create the transaction
    txn = transaction.ApplicationNoOpTxn(
        sender=account.address_from_private_key(private_key),
        sp=params,
        index=app_id,
        app_args=app_args,
        accounts=accounts if accounts else [],
        foreign_apps=foreign_apps if foreign_apps else [],
        foreign_assets=foreign_assets if foreign_assets else []
    )
    
    # Sign the transaction
    signed_txn = txn.sign(private_key)
    
    # Submit the transaction
    tx_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation
    result = _wait_for_confirmation(client, tx_id)
    
    return result

def _wait_for_confirmation(client, tx_id):
    """Wait for a transaction to be confirmed."""
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(tx_id)
    
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(tx_id)
    
    print(f"Transaction {tx_id} confirmed in round {txinfo.get('confirmed-round')}.")
    return txinfo

def fund_account(client, receiver_address, amount_algos):
    """
    Fund an account with Algos (useful for testing on testnet or private nets).
    """
    # In a real-world scenario, you'd have a funded account
    # For testnet, you can use the testnet dispenser
    print(f"Fund the account {receiver_address} with {amount_algos} Algos using the Algorand testnet dispenser:")
    print("https://bank.testnet.algorand.network/")

def create_test_account():
    """Create a new test account and display its information."""
    private_key, address = account.generate_account()
    mnem = mnemonic.from_private_key(private_key)
    
    print(f"\n--- Created New Test Account ---")
    print(f"Address: {address}")
    print(f"Private Key: {private_key}")
    print(f"Mnemonic: {mnem}")
    
    return private_key, address, mnem

def main():
    # Check if we should use an existing account
    use_existing = input("Do you want to use an existing account? (y/n): ").lower() == 'y'
    
    if use_existing:
        # Ask for private key or mnemonic
        key_input = input("Enter private key or mnemonic: ")
        
        # Determine if it's a private key or mnemonic
        if len(key_input.split()) > 1:
            # It's a mnemonic
            private_key = mnemonic.to_private_key(key_input)
        else:
            # It's a private key
            private_key = key_input
        
        address = account.address_from_private_key(private_key)
        print(f"Using account: {address}")
    else:
        # Generate a new account for testing
        private_key, address, _ = create_test_account()
    
    # Connect to Algorand client
    algod_address = os.environ.get("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
    algod_token = os.environ.get("ALGOD_TOKEN", "")
    client = algod.AlgodClient(algod_token, algod_address)
    
    # Check account balance
    try:
        account_info = client.account_info(address)
        balance = account_info.get('amount', 0) / 1000000  # Convert microAlgos to Algos
        print(f"Account balance: {balance} Algos")
        
        if balance < 10:
            # Fund the account (for testnet)
            fund_account(client, address, 10)
            input("Press Enter after funding the account to continue (or Ctrl+C to cancel)...")
    except Exception as e:
        print(f"Error checking account balance: {str(e)}")
        fund_account(client, address, 10)
        input("Press Enter after funding the account to continue (or Ctrl+C to cancel)...")
    
    # Deploy contracts
    app_ids = deploy_contracts(private_key)
    
    print("\nDeployment Complete!")
    print("\nContract Application IDs:")
    for name, app_id in app_ids.items():
        print(f"{name.capitalize()}: {app_id}")
    
    print("\nAdd these to your .env file:")
    for name, app_id in app_ids.items():
        print(f"{name.upper()}_APP_ID={app_id}")
    
    print(f"ADMIN_PRIVATE_KEY={private_key}")
    print(f"ADMIN_ADDRESS={address}")
    print("\nUse these App IDs when initializing the Document Execution Client SDK.")

if __name__ == "__main__":
    main()