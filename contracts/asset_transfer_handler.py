from pyteal import *

"""
Action Handler: Asset Transfer Implementation

Purpose: Handle the transfer of ASA (Algorand Standard Assets) after an agreement is executed.
This is another example action handler that can be registered with the Execution Router.
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
    REGISTER_ASSET_CONFIG = Bytes("register_asset_config")
    
    # Storage prefixes
    ASSET_ID_PREFIX = Bytes("asset_id_")      # For storing asset ID by agreement ID
    ASSET_AMOUNT_PREFIX = Bytes("amount_")    # For storing asset amount by agreement ID
    ASSET_SENDER_PREFIX = Bytes("sender_")    # For storing asset sender by agreement ID
    ASSET_RECEIVER_PREFIX = Bytes("receiver_")  # For storing asset receiver by agreement ID
    
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
    
    # Register asset transfer configuration for an agreement (admin only)
    # Args: agreement_id (uint), asset_id (uint), amount (uint), sender (address), receiver (address)
    on_register_asset_config = Seq([
        Assert(Txn.application_args.length() == Int(6)),
        Assert(is_admin),
        
        # Store the asset configuration for this agreement
        App.globalPut(
            Concat(ASSET_ID_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[2]  # asset_id
        ),
        
        App.globalPut(
            Concat(ASSET_AMOUNT_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[3]  # amount
        ),
        
        App.globalPut(
            Concat(ASSET_SENDER_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[4]  # sender
        ),
        
        App.globalPut(
            Concat(ASSET_RECEIVER_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[5]  # receiver
        ),
        
        # Log asset configuration registration
        Log(Concat(Bytes("ASSET_CONFIG_REGISTERED:"), Txn.application_args[1])),
        Log(Concat(Bytes("ASSET_ID:"), Txn.application_args[2])),
        
        Return(Int(1))
    ])
    
    # Process an executed agreement by transferring assets
    # Args: agreement_id (uint), [optional: receiver_override (address)]
    on_process_agreement = Seq([
        Assert(Txn.application_args.length() >= Int(2)),  # At least process_agreement + agreement_id
        
        # Only the Execution Router or admin can call this
        Assert(Or(
            is_router,
            is_admin
        )),
        
        # Get the agreement ID
        App.localPut(Int(0), Bytes("agreement_id"), Txn.application_args[1]),
        
        # Check if asset configuration is registered for this agreement
        Assert(App.globalGet(Concat(ASSET_ID_PREFIX, Txn.application_args[1])) != Bytes("")),
        
        # Store asset configuration
        App.localPut(Int(0), Bytes("asset_id"), 
                    Btoi(App.globalGet(Concat(ASSET_ID_PREFIX, Txn.application_args[1])))),
        
        App.localPut(Int(0), Bytes("amount"), 
                    Btoi(App.globalGet(Concat(ASSET_AMOUNT_PREFIX, Txn.application_args[1])))),
        
        App.localPut(Int(0), Bytes("sender"), 
                    App.globalGet(Concat(ASSET_SENDER_PREFIX, Txn.application_args[1]))),
        
        # Check if a receiver override is provided
        App.localPut(
            Int(0), 
            Bytes("receiver"),
            If(
                Txn.application_args.length() > Int(2),
                # Use the provided receiver override
                Txn.application_args[2],
                # Use the configured receiver
                App.globalGet(Concat(ASSET_RECEIVER_PREFIX, Txn.application_args[1]))
            )
        ),
        
        # Execute asset transfer transaction
        # This assumes the sender account has opted into this application
        # and the application has authority to transfer the asset
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.sender: App.localGet(Int(0), Bytes("sender")),
            TxnField.xfer_asset: App.localGet(Int(0), Bytes("asset_id")),
            TxnField.asset_receiver: App.localGet(Int(0), Bytes("receiver")),
            TxnField.asset_amount: App.localGet(Int(0), Bytes("amount")),
            TxnField.note: Concat(Bytes("Asset transfer for agreement:"), Txn.application_args[1]),
            TxnField.fee: Int(0),  # Fee covered by outer txn
        }),
        InnerTxnBuilder.Submit(),
        
        # Log asset transfer
        Log(Concat(Bytes("ASSET_TRANSFERRED:"), Txn.application_args[1])),
        Log(Concat(Bytes("ASSET_ID:"), Itob(App.localGet(Int(0), Bytes("asset_id"))))),
        Log(Concat(Bytes("AMOUNT:"), Itob(App.localGet(Int(0), Bytes("amount"))))),
        Log(Concat(Bytes("RECIPIENT:"), App.localGet(Int(0), Bytes("receiver")))),
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == SET_ROUTER, on_set_router],
        [ACTION == REGISTER_ASSET_CONFIG, on_register_asset_config],
        [ACTION == PROCESS_AGREEMENT, on_process_agreement]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("asset_transfer_handler.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
        
    with open("asset_transfer_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)