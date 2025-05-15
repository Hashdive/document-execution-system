from pyteal import *

"""
Action Handler: Contract Deployment Implementation

Purpose: Deploy a new smart contract after an agreement is executed.
This is a more advanced action handler that can be registered with the Execution Router.
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
    REGISTER_CONTRACT = Bytes("register_contract")
    
    # Storage prefixes
    CONTRACT_APPROVAL_PREFIX = Bytes("approval_")  # For storing approval program by agreement ID
    CONTRACT_CLEAR_PREFIX = Bytes("clear_")        # For storing clear program by agreement ID
    GLOBAL_SCHEMA_PREFIX = Bytes("global_schema_")  # For storing global schema by agreement ID
    LOCAL_SCHEMA_PREFIX = Bytes("local_schema_")    # For storing local schema by agreement ID
    
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
    
    # Register contract deployment configuration for an agreement (admin only)
    # Args: agreement_id (uint), approval_program (bytes), clear_program (bytes), 
    #       global_ints (uint8), global_bytes (uint8), local_ints (uint8), local_bytes (uint8)
    on_register_contract = Seq([
        Assert(Txn.application_args.length() == Int(8)),
        Assert(is_admin),
        
        # Store the contract configuration for this agreement
        App.globalPut(
            Concat(CONTRACT_APPROVAL_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[2]  # approval_program
        ),
        
        App.globalPut(
            Concat(CONTRACT_CLEAR_PREFIX, Txn.application_args[1]),  # agreement_id
            Txn.application_args[3]  # clear_program
        ),
        
        # Store schema info as separate values to avoid string parsing
        App.globalPut(
            Concat(GLOBAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_ints")),  
            Txn.application_args[4]  # global_ints
        ),
        
        App.globalPut(
            Concat(GLOBAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_bytes")),  
            Txn.application_args[5]  # global_bytes
        ),
        
        App.globalPut(
            Concat(LOCAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_ints")),  
            Txn.application_args[6]  # local_ints
        ),
        
        App.globalPut(
            Concat(LOCAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_bytes")),  
            Txn.application_args[7]  # local_bytes
        ),
        
        # Log contract configuration registration
        Log(Concat(Bytes("CONTRACT_REGISTERED:"), Txn.application_args[1])),
        
        Return(Int(1))
    ])
    
    # Process an executed agreement by deploying a smart contract
    # Args: agreement_id (uint)
    on_process_agreement = Seq([
        Assert(Txn.application_args.length() >= Int(2)),  # At least process_agreement + agreement_id
        
        # Only the Execution Router or admin can call this
        Assert(Or(
            is_router,
            is_admin
        )),
        
        # Get the agreement ID
        App.localPut(Int(0), Bytes("agreement_id"), Txn.application_args[1]),
        
        # Check if contract configuration is registered for this agreement
        Assert(App.globalGet(Concat(CONTRACT_APPROVAL_PREFIX, Txn.application_args[1])) != Bytes("")),
        
        # Store contract configuration
        App.localPut(Int(0), Bytes("approval_program"), 
                    App.globalGet(Concat(CONTRACT_APPROVAL_PREFIX, Txn.application_args[1]))),
        
        App.localPut(Int(0), Bytes("clear_program"), 
                    App.globalGet(Concat(CONTRACT_CLEAR_PREFIX, Txn.application_args[1]))),
        
        # Get global schema components directly
        App.localPut(Int(0), Bytes("global_ints"), 
                    Btoi(App.globalGet(Concat(GLOBAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_ints"))))),
        
        App.localPut(Int(0), Bytes("global_bytes"), 
                    Btoi(App.globalGet(Concat(GLOBAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_bytes"))))),
        
        # Get local schema components directly
        App.localPut(Int(0), Bytes("local_ints"), 
                    Btoi(App.globalGet(Concat(LOCAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_ints"))))),
        
        App.localPut(Int(0), Bytes("local_bytes"), 
                    Btoi(App.globalGet(Concat(LOCAL_SCHEMA_PREFIX, Txn.application_args[1], Bytes("_bytes"))))),
        
        # Deploy the smart contract
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.ApplicationCall,
            TxnField.approval_program: App.localGet(Int(0), Bytes("approval_program")),
            TxnField.clear_state_program: App.localGet(Int(0), Bytes("clear_program")),
            TxnField.global_num_uints: App.localGet(Int(0), Bytes("global_ints")),
            TxnField.global_num_byte_slices: App.localGet(Int(0), Bytes("global_bytes")),
            TxnField.local_num_uints: App.localGet(Int(0), Bytes("local_ints")),
            TxnField.local_num_byte_slices: App.localGet(Int(0), Bytes("local_bytes")),
            TxnField.note: Concat(Bytes("Contract deployment for agreement:"), Txn.application_args[1]),
            TxnField.fee: Int(0),  # Fee covered by outer txn
        }),
        InnerTxnBuilder.Submit(),
        
        # Log contract deployment
        Log(Concat(Bytes("CONTRACT_DEPLOYED:"), Txn.application_args[1])),
        Log(Concat(Bytes("APP_ID:"), Itob(InnerTxn.created_application_id()))),
        
        Return(Int(1))
    ])
    
    # Main router logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [ACTION == SET_ROUTER, on_set_router],
        [ACTION == REGISTER_CONTRACT, on_register_contract],
        [ACTION == PROCESS_AGREEMENT, on_process_agreement]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("contract_deployment_handler.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
        
    with open("contract_deployment_handler_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)