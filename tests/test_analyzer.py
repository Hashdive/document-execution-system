#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from pyteal import *
from contracts.execution_router import approval_program as router_approval, clear_state_program as router_clear

def diagnose_action_type_validation():
    """Diagnose the action type validation in the Execution Router."""
    print("\n----- Diagnosing Action Type Validation in Execution Router -----")
    
    # Compile the approval program
    approval_teal = compileTeal(router_approval(), mode=Mode.Application, version=6)
    
    # Print relevant sections of the TEAL code
    print("\nLooking for action type validation...\n")
    
    # Look for sections that might contain action type validation
    validation_lines = []
    handler_lines = []
    action_type_lines = []
    
    for i, line in enumerate(approval_teal.splitlines()):
        # Find lines with assertion or comparison logic
        if ("assert" in line.lower() or "!=" in line or "==" in line) and not line.strip().startswith("//"):
            validation_lines.append((i, line))
        
        # Find lines related to action handlers
        if "handler" in line.lower() and not line.strip().startswith("//"):
            handler_lines.append((i, line))
        
        # Find lines related to action types
        if "action_type" in line.lower() and not line.strip().startswith("//"):
            action_type_lines.append((i, line))
    
    print(f"\n=== Found {len(validation_lines)} validation/assertion lines ===")
    for i, line in validation_lines:
        print(f"Line {i+1}: {line}")
    
    print(f"\n=== Found {len(handler_lines)} handler-related lines ===")
    for i, line in handler_lines:
        print(f"Line {i+1}: {line}")
    
    print(f"\n=== Found {len(action_type_lines)} action_type-related lines ===")
    for i, line in action_type_lines:
        print(f"Line {i+1}: {line}")
    
    # Look for execute_action function to see how it validates action types
    print("\n=== Looking for execute_action implementation ===")
    in_execute_action = False
    execute_action_lines = []
    
    for i, line in enumerate(approval_teal.splitlines()):
        if "execute_action" in line:
            in_execute_action = True
            execute_action_lines.append((i, line))
        elif in_execute_action and line.strip() == "":
            in_execute_action = False
        elif in_execute_action:
            execute_action_lines.append((i, line))
    
    if execute_action_lines:
        print(f"Found execute_action implementation with {len(execute_action_lines)} lines:")
        for i, line in execute_action_lines[:50]:  # Print first 50 lines
            print(f"Line {i+1}: {line}")
        if len(execute_action_lines) > 50:
            print(f"... and {len(execute_action_lines) - 50} more lines")
    else:
        print("Could not identify execute_action implementation")
    
    # Based on findings, suggest test fix
    print("\n=== Suggested Test Fix ===")
    print("Based on the above analysis, you should modify the test_execution_router_security function to match how action type validation is actually implemented in your code.")
    
    return True

if __name__ == "__main__":
    diagnose_action_type_validation()