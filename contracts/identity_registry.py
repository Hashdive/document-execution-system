from pyteal import *

"""
Identity Registry Application

Purpose: Associate real-world identities (email, DID, orgID) with blockchain wallets
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
    
    # Handle initialization
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        Return(Int(1))
    ])
    
    # ===== Helper Functions =====
    
    # Check if caller is a verifier
    is_verifier = App.globalGet(Bytes("verifier_").concat(Txn.sender()))
    
    # Check if caller is admin
    is_admin = Txn.sender() == App.globalGet(admin)

    # ===== Action Logic =====
    
    # Register an identity claim (anyone can register)
    # Args: claim_type (string), claim_value (string)
    on_register_identity = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        
        # Claim type and value
        App.localPut(Txn.sender(), 
                   Concat(Txn.application_args[1], Bytes("_"), Txn.application_args[2]), 
                   Int(1)),
                   
        # Identity is set but not verified initially
        App.localPut(Txn.sender(),
                   Concat(Txn.application_args[1], Bytes("_verified")),
                   Int(0)),
                   
        Return(Int(1))
    ])
    
    # Verify an identity claim (only callable by verifiers)
    # Args: wallet_to_verify (address), claim_type (string)
    on_verify_identity = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        Assert(is_verifier),
        
        # Get account to verify from the arguments
        App.localPut(Txn.application_args[1],
                   Concat(Txn.application_args[2], Bytes("_verified")),
                   Int(1)),
                   
        Return(Int(1))
    ])
    
    # Add a new verifier (admin only)
    # Args: new_verifier_address (address)
    on_add_verifier = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        App.globalPut(Bytes("verifier_").concat(Txn.application_args[1]), Int(1)),
        
        Return(Int(1))
    ])
    
    # Remove a verifier (admin only)
    # Args: verifier_address (address)
    on_remove_verifier = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        App.globalPut(Bytes("verifier_").concat(Txn.application_args[1]), Int(0)),
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == REGISTER_IDENTITY, on_register_identity],
        [ACTION == VERIFY_IDENTITY, on_verify_identity],
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