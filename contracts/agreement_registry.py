from pyteal import *

"""
Agreement Registry Application

Purpose: Store document hashes, maintain signer lists, track signature status,
and execute agreements once all signatures are verified.

Enhanced with production-ready execution verification.
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
    ADD_SIGNER = Bytes("add_signer")         # New action to support dynamic signers
    ADD_METADATA = Bytes("add_metadata")     # New action to add metadata to agreements
    SET_EXECUTION_ROUTER = Bytes("set_execution_router")  # New action to set execution router
    
    # Box prefixes
    AGREEMENT_PREFIX = Bytes("agreement_")    # For agreement details
    SIGNER_PREFIX = Bytes("signer_")          # For tracking signers and status
    META_PREFIX = Bytes("meta_")              # For additional metadata
    
    # Handle initialization
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        App.globalPut(agreement_counter, Int(0)),
        App.globalPut(Bytes("execution_router_id"), Int(0)),  # Initialize execution router app ID
        # Add log for initialization
        Log(Bytes("INIT:admin=")),
        Log(Txn.sender()),
        Return(Int(1))
    ])
    
    # ===== Helper Functions =====
    
    # Check if caller is a verifier
    is_verifier = App.globalGet(Concat(Bytes("verifier_"), Txn.sender()))
    
    # Check if caller is admin
    is_admin = Txn.sender() == App.globalGet(admin)
    
    # Get the next agreement ID
    get_next_agreement_id = App.globalGet(agreement_counter)
    
    # ===== Action Logic =====
    
    # Create a new agreement with indexed signer storage
    # Args: document_hash (bytes32), provider (string), signers[] (addresses, passed as application arguments)
    on_create_agreement = Seq([
        Assert(Txn.application_args.length() >= Int(4)),  # Action + doc_hash + provider + at least one signer
        
        # Get new agreement ID
        App.globalPut(Bytes("temp_id"), get_next_agreement_id),
        # Increment the counter
        App.globalPut(agreement_counter, get_next_agreement_id + Int(1)),
        
        # Store ID in local state for this tx
        App.localPut(Int(0), Bytes("temp_id"), get_next_agreement_id),
        
        # Create agreement with document hash and provider
        # Format: {doc_hash, provider, timestamp, executed_flag}
        App.globalPut(
            Concat(AGREEMENT_PREFIX, Itob(get_next_agreement_id)),
            Concat(
                Txn.application_args[1],  # document_hash
                Txn.application_args[2],  # provider
                Itob(Global.latest_timestamp()),  # Creation timestamp
                Bytes("0")  # executed flag (0 = not executed)
            )
        ),
        
        # NEW: Store signers by index for easier verification
        # First signer (required)
        App.globalPut(
            Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_signer_1"))),
            Txn.application_args[3]  # First signer address
        ),
        
        # Also store in the original signer map for backward compatibility
        App.globalPut(
            Concat(SIGNER_PREFIX, Concat(Itob(get_next_agreement_id), Txn.application_args[3])),
            Bytes("0") # 0 = not signed
        ),
        Log(Concat(Bytes("SIGNER_ADDED:"), Concat(Itob(get_next_agreement_id), Txn.application_args[3]))),
        
        # For second signer (if exists)
        If(Txn.application_args.length() >= Int(5),
           Seq([
               # Store by index
               App.globalPut(
                   Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_signer_2"))),
                   Txn.application_args[4]  # Second signer address
               ),
               
               # Original storage
               App.globalPut(
                   Concat(SIGNER_PREFIX, Concat(Itob(get_next_agreement_id), Txn.application_args[4])),
                   Bytes("0") # 0 = not signed
               ),
               Log(Concat(Bytes("SIGNER_ADDED:"), Concat(Itob(get_next_agreement_id), Txn.application_args[4])))
           ])
        ),
        
        # For third signer (if exists)
        If(Txn.application_args.length() >= Int(6),
           Seq([
               # Store by index
               App.globalPut(
                   Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_signer_3"))),
                   Txn.application_args[5]  # Third signer address
               ),
               
               # Original storage
               App.globalPut(
                   Concat(SIGNER_PREFIX, Concat(Itob(get_next_agreement_id), Txn.application_args[5])),
                   Bytes("0") # 0 = not signed
               ),
               Log(Concat(Bytes("SIGNER_ADDED:"), Concat(Itob(get_next_agreement_id), Txn.application_args[5])))
           ])
        ),
        
        # For fourth signer (if exists)
        If(Txn.application_args.length() >= Int(7),
           Seq([
               # Store by index
               App.globalPut(
                   Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_signer_4"))),
                   Txn.application_args[6]  # Fourth signer address
               ),
               
               # Original storage
               App.globalPut(
                   Concat(SIGNER_PREFIX, Concat(Itob(get_next_agreement_id), Txn.application_args[6])),
                   Bytes("0") # 0 = not signed
               ),
               Log(Concat(Bytes("SIGNER_ADDED:"), Concat(Itob(get_next_agreement_id), Txn.application_args[6])))
           ])
        ),
        
        # For fifth signer (if exists)
        If(Txn.application_args.length() >= Int(8),
           Seq([
               # Store by index
               App.globalPut(
                   Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_signer_5"))),
                   Txn.application_args[7]  # Fifth signer address
               ),
               
               # Original storage
               App.globalPut(
                   Concat(SIGNER_PREFIX, Concat(Itob(get_next_agreement_id), Txn.application_args[7])),
                   Bytes("0") # 0 = not signed
               ),
               Log(Concat(Bytes("SIGNER_ADDED:"), Concat(Itob(get_next_agreement_id), Txn.application_args[7])))
           ])
        ),
        
        # Add to signer count
        App.globalPut(
            Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_signer_count"))), 
            If(
                Txn.application_args.length() - Int(3) > Int(5),
                Int(5),  # Maximum of 5 signers in this implementation
                Txn.application_args.length() - Int(3)  # Actual number of signers
            )
        ),
        
        # Store creation metadata
        App.globalPut(
            Concat(META_PREFIX, Concat(Itob(get_next_agreement_id), Bytes("_creator"))),
            Txn.sender()  # Store who created the agreement
        ),
        
        # Log the agreement creation
        Log(Concat(Bytes("AGREEMENT_CREATED:"), Itob(get_next_agreement_id))),
        Log(Concat(Bytes("PROVIDER:"), Txn.application_args[2])),
        
        Return(Int(1))
    ])
    
    # Add a signer to an existing agreement with indexed references
    # Args: agreement_id (uint), signer_wallet (address)
    on_add_signer = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        
        # Check that the caller is admin or agreement creator
        Assert(
            Or(
                is_admin,
                Txn.sender() == App.globalGet(
                    Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_creator")))
                )
            )
        ),
        
        # Check that agreement exists and is not executed
        Assert(App.globalGet(Concat(AGREEMENT_PREFIX, Txn.application_args[1])) != Bytes("")),
        Assert(
            Substring(
                App.globalGet(Concat(AGREEMENT_PREFIX, Txn.application_args[1])), 
                Int(64), # Position of executed flag (after hash and provider)
                Int(65)
            ) == Bytes("0")
        ),
        
        # Check if signer already exists
        Assert(
            App.globalGet(
                Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], Txn.application_args[2]))
            ) == Bytes("")
        ),
        
        # Get current signer count
        App.localPut(Int(0), Bytes("current_count"),
                    App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_count"))))),
        
        # Check max signer limit
        Assert(App.localGet(Int(0), Bytes("current_count")) < Int(5)),  # Max 5 signers in this implementation
        
        # Calculate new signer index
        App.localPut(Int(0), Bytes("new_index"), App.localGet(Int(0), Bytes("current_count")) + Int(1)),
        
        # Store signer in indexed reference
        App.globalPut(
            Concat(META_PREFIX, Concat(Txn.application_args[1], 
                                      Concat(Bytes("_signer_"), Itob(App.localGet(Int(0), Bytes("new_index")))))),
            Txn.application_args[2]  # New signer address
        ),
        
        # Original signer storage
        App.globalPut(
            Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], Txn.application_args[2])),
            Bytes("0") # 0 = not signed
        ),
        
        # Update signer count
        App.globalPut(
            Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_count"))),
            App.localGet(Int(0), Bytes("new_index"))
        ),
        
        # Log signer addition
        Log(Concat(Bytes("SIGNER_ADDED:"), Concat(Txn.application_args[1], Txn.application_args[2]))),
        
        Return(Int(1))
    ])
    
    # Add metadata to an agreement (admin or creator only)
    # Args: agreement_id (uint), metadata_key (string), metadata_value (string)
    on_add_metadata = Seq([
        Assert(Txn.application_args.length() == Int(4)),
        
        # Check that the caller is admin or agreement creator
        Assert(
            Or(
                is_admin,
                Txn.sender() == App.globalGet(
                    Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_creator")))
                )
            )
        ),
        
        # Check that agreement exists
        Assert(App.globalGet(Concat(AGREEMENT_PREFIX, Txn.application_args[1])) != Bytes("")),
        
        # Add metadata
        App.globalPut(
            Concat(META_PREFIX, Concat(Txn.application_args[1], Concat(Bytes("_"), Txn.application_args[2]))),
            Txn.application_args[3]
        ),
        
        # Log metadata addition
        Log(Concat(Bytes("METADATA_ADDED:"), Concat(Txn.application_args[1], Concat(Bytes(":"), Txn.application_args[2])))),
        
        Return(Int(1))
    ])
    
    # Mark an agreement as signed by a specific wallet
    # Args: agreement_id (uint), signer_wallet (address)
    on_mark_signed = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        Assert(is_verifier),  # Only verifiers can mark as signed
        
        # Check that agreement exists
        Assert(App.globalGet(Concat(AGREEMENT_PREFIX, Txn.application_args[1])) != Bytes("")),
        
        # Check that signer is registered for agreement
        Assert(App.globalGet(Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], Txn.application_args[2]))) != Bytes("")),
        
        # Mark as signed
        App.globalPut(
            Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], Txn.application_args[2])),
            Bytes("1")  # 1 = signed
        ),
        
        # Store signature timestamp
        App.globalPut(
            Concat(META_PREFIX, Concat(Txn.application_args[1], Concat(Bytes("_signed_at_"), Txn.application_args[2]))),
            Itob(Global.latest_timestamp())
        ),
        
        # Log signature event
        Log(Concat(Bytes("SIGNATURE:"), Concat(Txn.application_args[1], Concat(Bytes(":"), Txn.application_args[2])))),
        Log(Concat(Bytes("TIMESTAMP:"), Itob(Global.latest_timestamp()))),
        
        Return(Int(1))
    ])
    
    # Production-ready implementation of agreement execution verification
    # Args: agreement_id (uint)
    on_execute_agreement = Seq([
        Assert(Txn.application_args.length() == Int(2)),  # Action + agreement_id
        
        # Store agreement ID
        App.localPut(Int(0), Bytes("agreement_id"), Txn.application_args[1]),
        
        # Get agreement information
        Assert(App.globalGet(Concat(AGREEMENT_PREFIX, Txn.application_args[1])) != Bytes("")),
        
        # Store agreement data for this tx
        App.localPut(Int(0), Bytes("agreement_data"), 
                     App.globalGet(Concat(AGREEMENT_PREFIX, Txn.application_args[1]))),
        
        # Check if agreement is already executed
        Assert(
            Substring(
                App.localGet(Int(0), Bytes("agreement_data")), 
                Int(64), # Position after doc_hash and provider
                Int(65)
            ) == Bytes("0")
        ),
        
        # Get total signer count
        App.localPut(Int(0), Bytes("total_signers"),
                     App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_count"))))),
        
        # Initialize signed counter and verification flag
        App.localPut(Int(0), Bytes("signed_count"), Int(0)),
        App.localPut(Int(0), Bytes("all_signed"), Int(1)),  # Assume all signed until proven otherwise
        
        # Retrieve each potential signer and check if they signed
        # Check signer 1 (always required)
        If(
            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_1")))) != Bytes(""),
            Seq([
                # Store signer address
                App.localPut(Int(0), Bytes("current_signer"), 
                             App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_1"))))),
                
                # Check if this signer has signed
                If(
                    App.globalGet(
                        Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], 
                                              App.localGet(Int(0), Bytes("current_signer"))))
                    ) == Bytes("1"),  # If signed
                    # Increment signed count
                    App.localPut(Int(0), Bytes("signed_count"), App.localGet(Int(0), Bytes("signed_count")) + Int(1)),
                    # Else, mark not all signed
                    App.localPut(Int(0), Bytes("all_signed"), Int(0))
                )
            ])
        ),
        
        # Check signer 2 (if exists)
        If(
            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_2")))) != Bytes(""),
            Seq([
                # Store signer address
                App.localPut(Int(0), Bytes("current_signer"), 
                             App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_2"))))),
                
                # Check if this signer has signed
                If(
                    App.globalGet(
                        Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], 
                                              App.localGet(Int(0), Bytes("current_signer"))))
                    ) == Bytes("1"),  # If signed
                    # Increment signed count
                    App.localPut(Int(0), Bytes("signed_count"), App.localGet(Int(0), Bytes("signed_count")) + Int(1)),
                    # Else, mark not all signed
                    App.localPut(Int(0), Bytes("all_signed"), Int(0))
                )
            ])
        ),
        
        # Check signer 3 (if exists)
        If(
            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_3")))) != Bytes(""),
            Seq([
                # Store signer address
                App.localPut(Int(0), Bytes("current_signer"), 
                             App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_3"))))),
                
                # Check if this signer has signed
                If(
                    App.globalGet(
                        Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], 
                                              App.localGet(Int(0), Bytes("current_signer"))))
                    ) == Bytes("1"),  # If signed
                    # Increment signed count
                    App.localPut(Int(0), Bytes("signed_count"), App.localGet(Int(0), Bytes("signed_count")) + Int(1)),
                    # Else, mark not all signed
                    App.localPut(Int(0), Bytes("all_signed"), Int(0))
                )
            ])
        ),
        
        # Check signer 4 (if exists)
        If(
            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_4")))) != Bytes(""),
            Seq([
                # Store signer address
                App.localPut(Int(0), Bytes("current_signer"), 
                             App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_4"))))),
                
                # Check if this signer has signed
                If(
                    App.globalGet(
                        Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], 
                                              App.localGet(Int(0), Bytes("current_signer"))))
                    ) == Bytes("1"),  # If signed
                    # Increment signed count
                    App.localPut(Int(0), Bytes("signed_count"), App.localGet(Int(0), Bytes("signed_count")) + Int(1)),
                    # Else, mark not all signed
                    App.localPut(Int(0), Bytes("all_signed"), Int(0))
                )
            ])
        ),
        
        # Check signer 5 (if exists)
        If(
            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_5")))) != Bytes(""),
            Seq([
                # Store signer address
                App.localPut(Int(0), Bytes("current_signer"), 
                             App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_signer_5"))))),
                
                # Check if this signer has signed
                If(
                    App.globalGet(
                        Concat(SIGNER_PREFIX, Concat(Txn.application_args[1], 
                                              App.localGet(Int(0), Bytes("current_signer"))))
                    ) == Bytes("1"),  # If signed
                    # Increment signed count
                    App.localPut(Int(0), Bytes("signed_count"), App.localGet(Int(0), Bytes("signed_count")) + Int(1)),
                    # Else, mark not all signed
                    App.localPut(Int(0), Bytes("all_signed"), Int(0))
                )
            ])
        ),
        
        # Verify all have signed using both methods
        # Method 1: Check via all_signed flag 
        Assert(App.localGet(Int(0), Bytes("all_signed")) == Int(1)),
        
        # Method 2: Check via signed count match
        Assert(App.localGet(Int(0), Bytes("signed_count")) == App.localGet(Int(0), Bytes("total_signers"))),
        
        # Store the number of signers for logging
        App.localPut(Int(0), Bytes("signer_count"), App.localGet(Int(0), Bytes("total_signers"))),
        
        # Update executed flag
        App.globalPut(
            Concat(AGREEMENT_PREFIX, Txn.application_args[1]),
            Concat(
                Substring(App.localGet(Int(0), Bytes("agreement_data")), Int(0), Int(64)),
                Bytes("1"),  # Set executed flag to 1
                Itob(Global.latest_timestamp())  # Execution timestamp
            )
        ),
        
        # Store execution metadata
        App.globalPut(
            Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_executed_at"))),
            Itob(Global.latest_timestamp())
        ),
        App.globalPut(
            Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_executed_by"))),
            Txn.sender()
        ),
        
        # Execution Router Integration
        If(
            App.globalGet(Bytes("execution_router_id")) != Int(0),
            Seq([
                # Call the Execution Router
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.application_id: App.globalGet(Bytes("execution_router_id")),
                    TxnField.application_args: [
                        Bytes("execute_action"),
                        Txn.application_args[1],  # Agreement ID
                        # Action type from metadata (if exists)
                        If(
                            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_action_type")))) != Bytes(""),
                            App.globalGet(Concat(META_PREFIX, Concat(Txn.application_args[1], Bytes("_action_type")))),
                            Bytes("default")  # Default action type
                        )
                    ],
                    TxnField.note: Bytes("Agreement executed - calling router"),
                    TxnField.fee: Int(0),  # Fee covered by outer txn
                }),
                InnerTxnBuilder.Submit(),
                
                # Log router call
                Log(Bytes("EXECUTION_ROUTER_CALLED"))
            ])
        ),
        
        # Emit detailed log for executed agreement
        Log(Concat(Bytes("EXECUTED:"), Txn.application_args[1])),
        Log(Concat(Bytes("TIMESTAMP:"), Itob(Global.latest_timestamp()))),
        Log(Concat(Bytes("SIGNER_COUNT:"), Itob(App.localGet(Int(0), Bytes("signer_count"))))),
        
        Return(Int(1))
    ])
    
    # Set the execution router application ID (admin only)
    # Args: router_app_id (uint64)
    on_set_execution_router = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),  # Only admin can set the router
        
        # Set the router app ID
        App.globalPut(Bytes("execution_router_id"), Btoi(Txn.application_args[1])),
        
        # Log router setting
        Log(Concat(Bytes("EXECUTION_ROUTER_SET:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Add a new verifier (admin only)
    # Args: new_verifier_address (address)
    on_add_verifier = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        App.globalPut(Concat(Bytes("verifier_"), Txn.application_args[1]), Int(1)),
        
        # Log verifier addition
        Log(Concat(Bytes("VERIFIER_ADDED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Remove a verifier (admin only)
    # Args: verifier_address (address)
    on_remove_verifier = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        App.globalPut(Concat(Bytes("verifier_"), Txn.application_args[1]), Int(0)),
        
        # Log verifier removal
        Log(Concat(Bytes("VERIFIER_REMOVED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == CREATE_AGREEMENT, on_create_agreement],
        [ACTION == ADD_SIGNER, on_add_signer],
        [ACTION == ADD_METADATA, on_add_metadata],
        [ACTION == MARK_SIGNED, on_mark_signed],
        [ACTION == EXECUTE_AGREEMENT, on_execute_agreement],
        [ACTION == ADD_VERIFIER, on_add_verifier],
        [ACTION == REMOVE_VERIFIER, on_remove_verifier],
        [ACTION == SET_EXECUTION_ROUTER, on_set_execution_router]
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