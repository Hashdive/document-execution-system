from pyteal import *

"""
Agreement Registry Application

Purpose: Store document hashes, maintain signer lists, track signature status,
and execute agreements once all signatures are verified.
"""

def approval_program():
    # Global state variables
    admin = Bytes("admin")  # Admin who can manage the application
    agreement_counter = Bytes("agreement_counter")  # Tracks total agreements
    
    # Define application arguments indices
    ACTION = Txn.application_args[0]
    
    # Actions
    CREATE_AGREEMENT = Bytes("create_agreement")
    MARK_SIGNED = Bytes("mark_signed")
    EXECUTE_AGREEMENT = Bytes("execute_agreement")
    ADD_VERIFIER = Bytes("add_verifier")
    REMOVE_VERIFIER = Bytes("remove_verifier")
    
    # Box prefixes
    AGREEMENT_PREFIX = Bytes("agreement_")
    SIGNER_PREFIX = Bytes("signer_")
    
    # Handle initialization
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        App.globalPut(agreement_counter, Int(0)),
        Return(Int(1))
    ])
    
    # ===== Helper Functions =====
    
    # Check if caller is a verifier
    is_verifier = App.globalGet(Bytes("verifier_").concat(Txn.sender()))
    
    # Check if caller is admin
    is_admin = Txn.sender() == App.globalGet(admin)
    
    # Get the next agreement ID and increment counter
    get_next_agreement_id = Seq([
        App.globalGet(agreement_counter),
        App.globalPut(agreement_counter, App.globalGet(agreement_counter) + Int(1))
    ])
    
    # ===== Action Logic =====
    
    # Create a new agreement
    # Args: document_hash (bytes32), provider (string), signers[] (addresses, passed as application arguments)
    on_create_agreement = Seq([
        Assert(Txn.application_args.length() >= Int(4)),  # Action + doc_hash + provider + at least one signer
        
        # Get new agreement ID
        App.globalPut(Bytes("temp_id"), get_next_agreement_id),
        App.localPut(Int(0), Bytes("temp_id"), App.globalGet(Bytes("temp_id"))),
        
        # Create agreement box with document hash and provider
        # Format: {doc_hash, provider, executed_flag}
        App.boxPut(
            AGREEMENT_PREFIX.concat(Itob(App.globalGet(Bytes("temp_id")))),
            Concat(
                Txn.application_args[1],  # document_hash
                Txn.application_args[2],  # provider
                Bytes("0")  # executed flag (0 = not executed)
            )
        ),
        
        # Store signers and initialize as unsigned
        # Start from application_args[3] for signers
        # We'll use a separate loop in actual code to process all signers
        # For simplicity, here's how we'd handle a fixed number:
        
        # For first signer
        If(Txn.application_args.length() >= Int(4),
           App.boxPut(
               SIGNER_PREFIX.concat(Itob(App.globalGet(Bytes("temp_id")))).concat(Txn.application_args[3]),
               Bytes("0") # 0 = not signed
           )
        ),
        
        # Add similar lines for more signers...
        # In practice, you'd want a more flexible way to handle arbitrary numbers of signers
        
        Return(Int(1))
    ])
    
    # Mark an agreement as signed by a specific wallet
    # Args: agreement_id (uint), signer_wallet (address)
    on_mark_signed = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        Assert(is_verifier),  # Only verifiers can mark as signed
        
        # Check that agreement exists
        Assert(App.box_length(AGREEMENT_PREFIX.concat(Txn.application_args[1]))),
        
        # Check that signer is registered for agreement
        Assert(App.box_length(SIGNER_PREFIX.concat(Txn.application_args[1]).concat(Txn.application_args[2]))),
        
        # Mark as signed
        App.boxPut(
            SIGNER_PREFIX.concat(Txn.application_args[1]).concat(Txn.application_args[2]),
            Bytes("1")  # 1 = signed
        ),
        
        Return(Int(1))
    ])
    
    # Execute agreement if all signers have signed
    # Args: agreement_id (uint), signers[] (list of all signers to check)
    on_execute_agreement = Seq([
        Assert(Txn.application_args.length() >= Int(3)),  # Action + agreement_id + at least one signer
        
        # Get agreement information
        Assert(App.box_length(AGREEMENT_PREFIX.concat(Txn.application_args[1]))),
        
        # Verify all signers have signed
        # In practice, we'd loop through all signers - here's pseudocode for one:
        Assert(
            App.box_extract(
                SIGNER_PREFIX.concat(Txn.application_args[1]).concat(Txn.application_args[2]),
                Int(0),
                Int(1)
            ) == Bytes("1")
        ),
        
        # Add more checks for additional signers...
        
        # Mark agreement as executed
        # Extract current agreement data
        App.localPut(Int(0), Bytes("agreement_data"), 
                    App.box_extract(
                        AGREEMENT_PREFIX.concat(Txn.application_args[1]),
                        Int(0),
                        Int(64)  # Adjust based on your actual data size
                    )
        ),
        
        # Update executed flag
        App.boxPut(
            AGREEMENT_PREFIX.concat(Txn.application_args[1]),
            Concat(
                Substring(App.localGet(Int(0), Bytes("agreement_data")), Int(0), Int(63)),
                Bytes("1")  # Set executed flag to 1
            )
        ),
        
        # Emit log for executed agreement
        Log(Concat(Bytes("EXECUTED:"), Txn.application_args[1])),
        
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
        [ACTION == CREATE_AGREEMENT, on_create_agreement],
        [ACTION == MARK_SIGNED, on_mark_signed],
        [ACTION == EXECUTE_AGREEMENT, on_execute_agreement],
        [ACTION == ADD_VERIFIER, on_add_verifier],
        [ACTION == REMOVE_VERIFIER, on_remove_verifier]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("agreement_registry_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
        
    with open("agreement_registry_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)