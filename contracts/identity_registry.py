from pyteal import *

"""
Identity Registry Application

Purpose: Associate real-world identities (email, DID, orgID) with blockchain wallets
and enable verification by trusted oracles/validators.
"""

def approval_program():
    # Global state variables
    admin = Bytes("admin")  # Admin account that can add verifiers
    
    # Define application arguments indices
    ACTION = Txn.application_args[0]
    
    # Actions
    REGISTER_IDENTITY = Bytes("register_identity")
    VERIFY_IDENTITY = Bytes("verify_identity")
    ADD_VERIFIER = Bytes("add_verifier")
    REMOVE_VERIFIER = Bytes("remove_verifier")
    REVOKE_IDENTITY = Bytes("revoke_identity")       # New action to revoke identity claims
    UPDATE_CLAIM = Bytes("update_claim")             # New action to update identity claims
    
    # Prefixes for storage
    IDENTITY_PREFIX = Bytes("id_")  # For reverse lookups (claim_type:value → wallet)
    VERIFIER_PREFIX = Bytes("verifier_")  # For verifier management
    
    # Claim types (for logging and validation)
    CLAIM_EMAIL = Bytes("email")
    CLAIM_DID = Bytes("DID") 
    CLAIM_ORGID = Bytes("orgId")
    
    # Handle initialization
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        # Log initialization
        Log(Bytes("INIT:admin=")),
        Log(Txn.sender()),
        Return(Int(1))
    ])
    
    # ===== Helper Functions =====
    
    # Check if caller is a verifier
    is_verifier = App.globalGet(Concat(VERIFIER_PREFIX, Txn.sender()))
    
    # Check if caller is admin
    is_admin = Txn.sender() == App.globalGet(admin)
    
    # ===== Action Logic =====
    
    # Register an identity claim (anyone can register)
    # Args: claim_type (string), claim_value (string)
    on_register_identity = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        
        # Store claim type and value in local state
        App.localPut(
            Int(0),  # Current account
            Concat(Txn.application_args[1], Bytes("_"), Txn.application_args[2]), 
            Int(1)
        ),
        
        # Set verification status to unverified
        App.localPut(
            Int(0),  # Current account
            Concat(Txn.application_args[1], Bytes("_verified")),
            Int(0)
        ),
        
        # Store registration timestamp
        App.localPut(
            Int(0),  # Current account
            Concat(Txn.application_args[1], Bytes("_registered_at")),
            Global.latest_timestamp()
        ),
        
        # Store reverse lookup in global state (claim_type:value → wallet)
        # This allows looking up wallets by identity
        App.globalPut(
            Concat(IDENTITY_PREFIX, Concat(Txn.application_args[1], Concat(Bytes(":"), Txn.application_args[2]))),
            Txn.sender()
        ),
        
        # Log identity registration
        Log(Concat(Bytes("IDENTITY_REGISTERED:"), Txn.sender())),
        Log(Concat(Bytes("CLAIM_TYPE:"), Txn.application_args[1])),
        Log(Concat(Bytes("CLAIM_VALUE:"), Txn.application_args[2])),
        
        Return(Int(1))
    ])
    
    # Verify an identity claim (only callable by verifiers)
    # Args: wallet_to_verify (address), claim_type (string)
    on_verify_identity = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        Assert(is_verifier),  # Only verifiers can verify identities
        
        # Set verification status to verified
        App.localPut(
            Txn.application_args[1],  # Account to verify
            Concat(Txn.application_args[2], Bytes("_verified")),
            Int(1)
        ),
        
        # Store verification timestamp
        App.localPut(
            Txn.application_args[1],  # Account to verify
            Concat(Txn.application_args[2], Bytes("_verified_at")),
            Global.latest_timestamp()
        ),
        
        # Store verifier information
        App.localPut(
            Txn.application_args[1],  # Account to verify
            Concat(Txn.application_args[2], Bytes("_verified_by")),
            Txn.sender()
        ),
        
        # Log verification
        Log(Concat(Bytes("IDENTITY_VERIFIED:"), Txn.application_args[1])),
        Log(Concat(Bytes("CLAIM_TYPE:"), Txn.application_args[2])),
        Log(Concat(Bytes("VERIFIER:"), Txn.sender())),
        
        Return(Int(1))
    ])
    
    # Update a claim value (must be done by the claim owner)
    # Args: old_claim_type (string), old_claim_value (string), new_claim_value (string)
    on_update_claim = Seq([
        Assert(Txn.application_args.length() == Int(4)),
        
        # Ensure the old claim exists for this wallet
        Assert(
            App.localGet(
                Int(0),  # Current account
                Concat(Txn.application_args[1], Bytes("_"), Txn.application_args[2])
            ) == Int(1)
        ),
        
        # Remove the old claim
        App.localDel(
            Int(0),  # Current account
            Concat(Txn.application_args[1], Bytes("_"), Txn.application_args[2])
        ),
        
        # Remove the old reverse lookup
        App.globalDel(
            Concat(IDENTITY_PREFIX, Concat(Txn.application_args[1], Concat(Bytes(":"), Txn.application_args[2])))
        ),
        
        # Add the new claim
        App.localPut(
            Int(0),  # Current account
            Concat(Txn.application_args[1], Bytes("_"), Txn.application_args[3]), 
            Int(1)
        ),
        
        # Reset verification status
        App.localPut(
            Int(0),  # Current account
            Concat(Txn.application_args[1], Bytes("_verified")),
            Int(0)
        ),
        
        # Add the new reverse lookup
        App.globalPut(
            Concat(IDENTITY_PREFIX, Concat(Txn.application_args[1], Concat(Bytes(":"), Txn.application_args[3]))),
            Txn.sender()
        ),
        
        # Log the update
        Log(Concat(Bytes("IDENTITY_UPDATED:"), Txn.sender())),
        Log(Concat(Bytes("CLAIM_TYPE:"), Txn.application_args[1])),
        Log(Concat(Bytes("OLD_VALUE:"), Txn.application_args[2])),
        Log(Concat(Bytes("NEW_VALUE:"), Txn.application_args[3])),
        
        Return(Int(1))
    ])
    
    # Revoke an identity claim (can be done by claim owner or verifier)
    # Args: wallet_address (address), claim_type (string), claim_value (string)
    on_revoke_identity = Seq([
        Assert(Txn.application_args.length() == Int(4)),
        
        # Check caller is either the wallet owner, a verifier, or admin
        Assert(
            Or(
                Txn.sender() == Txn.application_args[1],  # Wallet owner
                is_verifier,  # Verifier
                is_admin  # Admin
            )
        ),
        
        # Remove the claim
        App.localDel(
            Txn.application_args[1],  # Target account
            Concat(Txn.application_args[2], Bytes("_"), Txn.application_args[3])
        ),
        
        # Remove verification status
        App.localDel(
            Txn.application_args[1],  # Target account
            Concat(Txn.application_args[2], Bytes("_verified"))
        ),
        
        # Remove the reverse lookup
        App.globalDel(
            Concat(IDENTITY_PREFIX, Concat(Txn.application_args[2], Concat(Bytes(":"), Txn.application_args[3])))
        ),
        
        # Log revocation
        Log(Concat(Bytes("IDENTITY_REVOKED:"), Txn.application_args[1])),
        Log(Concat(Bytes("CLAIM_TYPE:"), Txn.application_args[2])),
        Log(Concat(Bytes("REVOKED_BY:"), Txn.sender())),
        
        Return(Int(1))
    ])
    
    # Add a new verifier (admin only)
    # Args: new_verifier_address (address)
    on_add_verifier = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),  # Only admin can add verifiers
        
        # Add verifier to global state
        App.globalPut(Concat(VERIFIER_PREFIX, Txn.application_args[1]), Int(1)),
        
        # Log verifier addition
        Log(Concat(Bytes("VERIFIER_ADDED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Remove a verifier (admin only)
    # Args: verifier_address (address)
    on_remove_verifier = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),  # Only admin can remove verifiers
        
        # Remove verifier from global state
        App.globalPut(Concat(VERIFIER_PREFIX, Txn.application_args[1]), Int(0)),
        
        # Log verifier removal
        Log(Concat(Bytes("VERIFIER_REMOVED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == REGISTER_IDENTITY, on_register_identity],
        [ACTION == VERIFY_IDENTITY, on_verify_identity],
        [ACTION == UPDATE_CLAIM, on_update_claim],
        [ACTION == REVOKE_IDENTITY, on_revoke_identity],
        [ACTION == ADD_VERIFIER, on_add_verifier],
        [ACTION == REMOVE_VERIFIER, on_remove_verifier]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("identity_registry_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
        
    with open("identity_registry_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)