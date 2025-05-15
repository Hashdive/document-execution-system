from pyteal import *

"""
Action Handler: Escrow Release Implementation

Purpose: Handle the release of escrowed funds after an agreement is executed.
This is an example action handler that can be registered with the Execution Router.
"""

def approval_program():
    # Global state variables
    admin = Bytes("admin")  # Admin who can manage the application
    router_id = Bytes("router_id")  # ID of the Execution Router app
    
    # Define application arguments indices
    ACTION = Txn.application_args[0]
    
    # Actions
    PROCESS_AGREEMENT = Bytes("process_agreement")
    SET_ROUTER = Bytes("set_router")
    REGISTER_ESCROW = Bytes("register_escrow")
    
    # Storage prefixes
    ESCROW_PREFIX = Bytes("escrow_")  # For storing escrow accounts by agreement ID
    
    # Handle initialization
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        App.globalPut(router_id, Int(0)),  # Will be set later
        
        # Log initialization
        Log(Bytes("INIT:admin=")),
        Log(Txn.sender()),
        Return(Int(1))
    ])
    
    # ===== Helper Functions =====
    
    # Check if caller is admin
    is_admin = Txn.sender() == App.globalGet(admin)
    
    # Check if caller is the execution router
    is_router = Txn.sender() == App.globalGet(router_id)
    
    # ===== Action Logic =====
    
    # Set the Execution Router ID (admin only)
    # Args: app_id (uint)
    on_set_router = Seq([
        Assert(Txn.application_args.length() == Int(2)),
        Assert(is_admin),
        
        App.globalPut(router_id, Btoi(Txn.application_args[1])),
        
        # Log update
        Log(Concat(Bytes("ROUTER_SET:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Register an escrow account for an agreement (admin only)
    # Args: agreement_id (uint), escrow_address (address)
    on_register_escrow = Seq([
        Assert(Txn.application_args.length() == Int(3)),
        Assert(is_admin),
        
        # Store the escrow account for this agreement
        App.globalPut(
            Concat(ESCROW_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[2]  # escrow_address
        ),
        
        # Log escrow registration
        Log(Concat(Bytes("ESCROW_REGISTERED:"), Txn.application_args[1])),
        Log(Concat(Bytes("ESCROW_ADDRESS:"), Txn.application_args[2])),
        
        Return(Int(1))
    ])
    
    # Process an executed agreement by releasing escrowed funds
    # Args: agreement_id (uint), [optional: recipient_override (address)]
    on_process_agreement = Seq([
        Assert(Txn.application_args.length() >= Int(2)),  # At least process_agreement + agreement_id
        
        # Only the Execution Router or admin can call this
        Assert(Or(
            is_router,
            is_admin
        )),
        
        # Get the agreement ID
        App.localPut(Int(0), Bytes("agreement_id"), Txn.application_args[1]),
        
        # Check if escrow account is registered for this agreement
        Assert(App.globalGet(Concat(ESCROW_PREFIX, Txn.application_args[1])) != Bytes("")),
        
        # Store escrow address
        App.localPut(Int(0), Bytes("escrow_address"), App.globalGet(Concat(ESCROW_PREFIX, Txn.application_args[1]))),
        
        # Check if a recipient override is provided
        App.localPut(
            Int(0), 
            Bytes("recipient"),
            If(
                Txn.application_args.length() > Int(2),
                # Use the provided recipient
                Txn.application_args[2],
                # Default to transaction sender
                Txn.sender()
            )
        ),
        
        # Execute payment transaction to release funds
        # This assumes the escrow account has opted into this application
        # and the application has authority to spend from the escrow
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.sender: App.localGet(Int(0), Bytes("escrow_address")),
            TxnField.receiver: App.localGet(Int(0), Bytes("recipient")),
            TxnField.amount: Int(1000000),  # Amount in microAlgos (1 Algo in this example)
            TxnField.note: Concat(Bytes("Escrow release for agreement:"), Txn.application_args[1]),
            TxnField.fee: Int(0),  # Fee covered by outer txn
        }),
        InnerTxnBuilder.Submit(),
        
        # Log escrow release
        Log(Concat(Bytes("ESCROW_RELEASED:"), Txn.application_args[1])),
        Log(Concat(Bytes("AMOUNT:"), Itob(Int(1000000)))),
        Log(Concat(Bytes("RECIPIENT:"), App.localGet(Int(0), Bytes("recipient")))),
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == SET_ROUTER, on_set_router],
        [ACTION == REGISTER_ESCROW, on_register_escrow],
        [ACTION == PROCESS_AGREEMENT, on_process_agreement]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("escrow_release_handler.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
        
    with open("escrow_release_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)