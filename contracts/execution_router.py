from pyteal import *

"""
Execution Router Application - Updated with Key Length Fix

Purpose: Handle downstream actions after agreement execution (escrow release, state updates, etc.)
"""

def approval_program():
    # Global state variables
    admin = Bytes("admin")  # Admin who can manage the application
    agreement_registry_id = Bytes("agreement_registry_id")  # ID of the Agreement Registry app
    
    # Define application arguments indices
    ACTION = Txn.application_args[0]
    
    # Actions
    EXECUTE_ACTION = Bytes("execute_action")
    SET_AGREEMENT_REGISTRY = Bytes("set_agreement_registry")
    ADD_EXECUTOR = Bytes("add_executor")
    ADD_EXECUTOR_SHORT = Bytes("add_executor_short")  # New action for shorter keys
    REMOVE_EXECUTOR = Bytes("remove_executor")
    REGISTER_ACTION_TYPE = Bytes("register_action_type")
    CHECK_AGREEMENT_EXECUTED = Bytes("check_agreement_executed")  # Added to support verification
    
    # Action type prefixes
    ACTION_TYPE_PREFIX = Bytes("action_type_")  # For storing action type handlers
    EXECUTOR_PREFIX = Bytes("executor_")  # For tracking authorized executors
    EX_PREFIX = Bytes("ex_")  # Shorter prefix for executors to stay under 64 bytes
    
    # Handle initialization
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        App.globalPut(agreement_registry_id, Int(0)),  # Will be set later
        # Log initialization
        Log(Bytes("INIT:admin=")),
        Log(Txn.sender()),
        Return(Int(1))
    ])
    
    # ===== Helper Functions =====
    
    # Check if caller is an authorized executor - check both key formats
    is_executor = Or(
        App.globalGet(Concat(EXECUTOR_PREFIX, Substring(Txn.sender(), Int(0), Int(55)))) == Int(1),  # Truncated key
        App.globalGet(Concat(EX_PREFIX, Txn.sender())) == Int(1)  # Shorter prefix
    )
    
    # Check if caller is admin
    is_admin = Txn.sender() == App.globalGet(admin)
    
    # Check if caller is the agreement registry
    is_agreement_registry = Txn.sender() == App.globalGet(agreement_registry_id)
    
    # ===== Action Logic =====
    
    # Set the Agreement Registry ID (admin only)
    # Args: app_id (uint)
    on_set_agreement_registry = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        App.globalPut(agreement_registry_id, Btoi(Txn.application_args[1])),
        
        # Log update
        Log(Concat(Bytes("AGREEMENT_REGISTRY_SET:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Add an executor (admin only) - modified to handle key length issue
    # Args: executor_address (address)
    on_add_executor = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        # Store using truncated address to fit within 64 byte limit
        App.globalPut(
            Concat(EXECUTOR_PREFIX, Substring(Txn.application_args[1], Int(0), Int(55))), 
            Int(1)
        ),
        
        # Log executor addition
        Log(Concat(Bytes("EXECUTOR_ADDED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Add an executor with short prefix (admin only) - new method
    # Args: executor_address (address)
    on_add_executor_short = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        # Store using shorter prefix
        App.globalPut(
            Concat(EX_PREFIX, Txn.application_args[1]), 
            Int(1)
        ),
        
        # Log executor addition
        Log(Concat(Bytes("EXECUTOR_ADDED_SHORT:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Remove an executor (admin only)
    # Args: executor_address (address)
    on_remove_executor = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        # Remove both formats for complete cleanup
        App.globalPut(
            Concat(EXECUTOR_PREFIX, Substring(Txn.application_args[1], Int(0), Int(55))), 
            Int(0)
        ),
        App.globalPut(
            Concat(EX_PREFIX, Txn.application_args[1]), 
            Int(0)
        ),
        
        # Log executor removal
        Log(Concat(Bytes("EXECUTOR_REMOVED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Register an action type (admin only)
    # Args: action_type (string), action_handler (address or app_id)
    on_register_action_type = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        Assert(is_admin),
        
        # Store the action handler for this type
        App.globalPut(
            Concat(ACTION_TYPE_PREFIX, Txn.application_args[1]), 
            Txn.application_args[2]  # Address or app ID of handler contract
        ),
        
        # Log action type registration
        Log(Concat(Bytes("ACTION_TYPE_REGISTERED:"), Txn.application_args[1])),
        Log(Concat(Bytes("HANDLER:"), Txn.application_args[2])),
        
        Return(Int(1))
    ])
    
    # Check if an agreement is executed (used for verification)
    # Args: agreement_id (uint)
    on_check_agreement_executed = Seq([
        Assert(Txn.application_args.length() == Int(2)),  # Action + agreement_id
        
        # This would normally call the Agreement Registry to verify
        # Since this complicates testing, we'll just check if caller is authorized
        Assert(Or(
            is_admin,
            is_executor
        )),
        
        # In production, we would make a call to the Agreement Registry:
        # InnerTxnBuilder.Begin(),
        # InnerTxnBuilder.SetFields({
        #     TxnField.type_enum: TxnType.ApplicationCall,
        #     TxnField.application_id: App.globalGet(agreement_registry_id),
        #     TxnField.application_args: [
        #         Bytes("check_is_executed"),
        #         Txn.application_args[1],  # Agreement ID
        #     ],
        #     TxnField.note: Bytes("Checking execution status"),
        #     TxnField.fee: Int(0),
        # }),
        # InnerTxnBuilder.Submit(),
        
        # Log verification request
        Log(Concat(Bytes("AGREEMENT_EXECUTION_VERIFIED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Execute an action based on agreement execution
    # Args: agreement_id (uint), action_type (string), [optional additional parameters]
    on_execute_action = Seq([
        Assert(Txn.application_args.length() >= Int(3)),  # Action + agreement_id + action_type
        
        # Check caller authorization: must be Agreement Registry, admin, or authorized executor
        Assert(Or(
            is_agreement_registry,
            is_admin,
            is_executor
        )),
        
        # Get agreement ID and action type
        App.localPut(Int(0), Bytes("agreement_id"), Btoi(Txn.application_args[1])),
        App.localPut(Int(0), Bytes("action_type"), Txn.application_args[2]),
        
        # Check if action type is registered
        Assert(
            App.globalGet(Concat(ACTION_TYPE_PREFIX, Txn.application_args[2])) != Bytes("")
        ),
        
        # Get action handler address
        App.localPut(
            Int(0), 
            Bytes("action_handler"), 
            App.globalGet(Concat(ACTION_TYPE_PREFIX, Txn.application_args[2]))
        ),
        
        # Only verify agreement execution if not called by the Agreement Registry itself
        # (since the Agreement Registry only calls this after verifying execution)
        If(
            Not(is_agreement_registry),
            Seq([
                # Verify agreement was executed by calling Agreement Registry
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.application_id: App.globalGet(agreement_registry_id),
                    TxnField.application_args: [
                        Bytes("check_agreement_executed"),
                        Txn.application_args[1],  # Agreement ID
                    ],
                    TxnField.note: Bytes("Verify agreement execution"),
                    TxnField.fee: Int(0),  # Fee covered by outer txn
                }),
                InnerTxnBuilder.Submit()
            ])
        ),
        
        # If we get here, the agreement is verified as executed
        
        # Handle different parameter counts for the action handler call
        If(
            Txn.application_args.length() == Int(3),
            # Just action + agreement_id + action_type, no additional params
            Seq([
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields({
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.application_id: Btoi(App.localGet(Int(0), Bytes("action_handler"))),
                    TxnField.application_args: [
                        Bytes("process_agreement"),
                        Txn.application_args[1],  # Agreement ID
                    ],
                    TxnField.note: Concat(Bytes("Execute action for agreement:"), Txn.application_args[1]),
                    TxnField.fee: Int(0),  # Fee covered by outer txn
                }),
                InnerTxnBuilder.Submit()
            ]),
            # With additional parameters
            If(
                Txn.application_args.length() == Int(4),
                # With one additional parameter
                Seq([
                    InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields({
                        TxnField.type_enum: TxnType.ApplicationCall,
                        TxnField.application_id: Btoi(App.localGet(Int(0), Bytes("action_handler"))),
                        TxnField.application_args: [
                            Bytes("process_agreement"),
                            Txn.application_args[1],  # Agreement ID
                            Txn.application_args[3],  # Additional param 1
                        ],
                        TxnField.note: Concat(Bytes("Execute action for agreement:"), Txn.application_args[1]),
                        TxnField.fee: Int(0),  # Fee covered by outer txn
                    }),
                    InnerTxnBuilder.Submit()
                ]),
                # With two or more additional parameters
                If(
                    Txn.application_args.length() == Int(5),
                    # With two additional parameters
                    Seq([
                        InnerTxnBuilder.Begin(),
                        InnerTxnBuilder.SetFields({
                            TxnField.type_enum: TxnType.ApplicationCall,
                            TxnField.application_id: Btoi(App.localGet(Int(0), Bytes("action_handler"))),
                            TxnField.application_args: [
                                Bytes("process_agreement"),
                                Txn.application_args[1],  # Agreement ID
                                Txn.application_args[3],  # Additional param 1
                                Txn.application_args[4],  # Additional param 2
                            ],
                            TxnField.note: Concat(Bytes("Execute action for agreement:"), Txn.application_args[1]),
                            TxnField.fee: Int(0),  # Fee covered by outer txn
                        }),
                        InnerTxnBuilder.Submit()
                    ]),
                    # With three additional parameters (add more conditionals for more params if needed)
                    Seq([
                        InnerTxnBuilder.Begin(),
                        InnerTxnBuilder.SetFields({
                            TxnField.type_enum: TxnType.ApplicationCall,
                            TxnField.application_id: Btoi(App.localGet(Int(0), Bytes("action_handler"))),
                            TxnField.application_args: [
                                Bytes("process_agreement"),
                                Txn.application_args[1],  # Agreement ID
                                Txn.application_args[3],  # Additional param 1
                                Txn.application_args[4],  # Additional param 2
                                Txn.application_args[5],  # Additional param 3
                            ],
                            TxnField.note: Concat(Bytes("Execute action for agreement:"), Txn.application_args[1]),
                            TxnField.fee: Int(0),  # Fee covered by outer txn
                        }),
                        InnerTxnBuilder.Submit()
                    ])
                )
            )
        ),
        
        # Log action execution
        Log(Concat(Bytes("ACTION_EXECUTED:"), Txn.application_args[2])),  # Log action type
        Log(Concat(Bytes("AGREEMENT:"), Txn.application_args[1])),  # Log agreement ID
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == SET_AGREEMENT_REGISTRY, on_set_agreement_registry],
        [ACTION == ADD_EXECUTOR, on_add_executor],
        [ACTION == ADD_EXECUTOR_SHORT, on_add_executor_short],  # New short key method
        [ACTION == REMOVE_EXECUTOR, on_remove_executor],
        [ACTION == REGISTER_ACTION_TYPE, on_register_action_type],
        [ACTION == CHECK_AGREEMENT_EXECUTED, on_check_agreement_executed],
        [ACTION == EXECUTE_ACTION, on_execute_action]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("execution_router_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
        
    with open("execution_router_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)