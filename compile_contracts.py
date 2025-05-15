#!/usr/bin/env python3
import os
import sys
# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from pyteal import compileTeal, Mode

# Import the contracts
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
from contracts.closing_agreement import approval_program as closing_approval
from contracts.closing_agreement import clear_state_program as closing_clear_state

def compile_contracts():
    """
    Compile the smart contracts and save the TEAL files.
    """
    print("Compiling Identity Registry...")
    # Identity Registry
    try:
        identity_approval_teal = compileTeal(identity_approval(), mode=Mode.Application, version=6)
        identity_clear_state_teal = compileTeal(identity_clear_state(), mode=Mode.Application, version=6)
        with open("build/identity_registry_approval.teal", "w") as f:
            f.write(identity_approval_teal)
        with open("build/identity_registry_clear_state.teal", "w") as f:
            f.write(identity_clear_state_teal)
        print("✅ Identity Registry compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Identity Registry: {str(e)}")
        return False

    print("\nCompiling Agreement Registry...")
    # Agreement Registry
    try:
        agreement_approval_teal = compileTeal(agreement_approval(), mode=Mode.Application, version=6)
        agreement_clear_state_teal = compileTeal(agreement_clear_state(), mode=Mode.Application, version=6)
        with open("build/agreement_registry_approval.teal", "w") as f:
            f.write(agreement_approval_teal)
        with open("build/agreement_registry_clear_state.teal", "w") as f:
            f.write(agreement_clear_state_teal)
        print("✅ Agreement Registry compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Agreement Registry: {str(e)}")
        return False
    
    print("\nCompiling Execution Router...")
    # Execution Router
    try:
        router_approval_teal = compileTeal(router_approval(), mode=Mode.Application, version=6)
        router_clear_state_teal = compileTeal(router_clear_state(), mode=Mode.Application, version=6)
        with open("build/execution_router_approval.teal", "w") as f:
            f.write(router_approval_teal)
        with open("build/execution_router_clear_state.teal", "w") as f:
            f.write(router_clear_state_teal)
        print("✅ Execution Router compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Execution Router: {str(e)}")
        return False
    
    print("\nCompiling Escrow Release Handler...")
    # Escrow Release Handler
    try:
        escrow_approval_teal = compileTeal(escrow_approval(), mode=Mode.Application, version=6)
        escrow_clear_state_teal = compileTeal(escrow_clear_state(), mode=Mode.Application, version=6)
        with open("build/escrow_release_handler_approval.teal", "w") as f:
            f.write(escrow_approval_teal)
        with open("build/escrow_release_handler_clear_state.teal", "w") as f:
            f.write(escrow_clear_state_teal)
        print("✅ Escrow Release Handler compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Escrow Release Handler: {str(e)}")
        return False
    
    print("\nCompiling Asset Transfer Handler...")
    # Asset Transfer Handler
    try:
        asset_approval_teal = compileTeal(asset_approval(), mode=Mode.Application, version=6)
        asset_clear_state_teal = compileTeal(asset_clear_state(), mode=Mode.Application, version=6)
        with open("build/asset_transfer_handler_approval.teal", "w") as f:
            f.write(asset_approval_teal)
        with open("build/asset_transfer_handler_clear_state.teal", "w") as f:
            f.write(asset_clear_state_teal)
        print("✅ Asset Transfer Handler compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Asset Transfer Handler: {str(e)}")
        return False
    
    print("\nCompiling Contract Deployment Handler...")
    # Contract Deployment Handler
    try:
        deploy_approval_teal = compileTeal(deploy_approval(), mode=Mode.Application, version=6)
        deploy_clear_state_teal = compileTeal(deploy_clear_state(), mode=Mode.Application, version=6)
        with open("build/contract_deployment_handler_approval.teal", "w") as f:
            f.write(deploy_approval_teal)
        with open("build/contract_deployment_handler_clear_state.teal", "w") as f:
            f.write(deploy_clear_state_teal)
        print("✅ Contract Deployment Handler compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Contract Deployment Handler: {str(e)}")
        return False
    
    print("\nCompiling Closing Agreement...")
    # Closing Agreement
    try:
        closing_approval_teal = compileTeal(closing_approval(), mode=Mode.Application, version=6)
        closing_clear_state_teal = compileTeal(closing_clear_state(), mode=Mode.Application, version=6)
        with open("build/closing_agreement_approval.teal", "w") as f:
            f.write(closing_approval_teal)
        with open("build/closing_agreement_clear_state.teal", "w") as f:
            f.write(closing_clear_state_teal)
        print("✅ Closing Agreement compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling Closing Agreement: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Create build directory if it doesn't exist
    os.makedirs("build", exist_ok=True)
    
    # Compile contracts
    if compile_contracts():
        print("\n✅ All contracts compiled successfully!")
        print("TEAL files saved to the 'build' directory")
    else:
        print("\n❌ Compilation failed")
        sys.exit(1)