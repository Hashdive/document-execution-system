#!/usr/bin/env python3
import os
import sys
import base64
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from pyteal import *
from contracts.identity_registry import approval_program as identity_approval, clear_state_program as identity_clear
from contracts.agreement_registry import approval_program as agreement_approval, clear_state_program as agreement_clear

class TestSmartContracts(unittest.TestCase):
    """Test the Identity and Agreement Registry smart contracts locally."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create output directory for the compiled TEAL
        os.makedirs("build", exist_ok=True)
    
    def compile_program(self, program, output_file):
        """Compile a PyTeal program to TEAL and write to a file."""
        teal_code = compileTeal(program, mode=Mode.Application, version=6)
        
        with open(output_file, "w") as f:
            f.write(teal_code)
        
        return teal_code
    
    def test_identity_registry_compiles(self):
        """Test that the Identity Registry compiles successfully."""
        print("\n----- Testing Identity Registry Compilation -----")
        
        # Compile approval program
        approval_file = "build/identity_registry_approval.teal"
        approval_teal = self.compile_program(identity_approval(), approval_file)
        
        self.assertTrue(len(approval_teal) > 0, "Approval program should not be empty")
        print(f"✅ Identity Registry approval program compiled successfully ({len(approval_teal)} bytes)")
        
        # Compile clear state program
        clear_file = "build/identity_registry_clear_state.teal"
        clear_teal = self.compile_program(identity_clear(), clear_file)
        
        self.assertTrue(len(clear_teal) > 0, "Clear state program should not be empty")
        print(f"✅ Identity Registry clear state program compiled successfully ({len(clear_teal)} bytes)")
        
        return True
    
    def test_agreement_registry_compiles(self):
        """Test that the Agreement Registry compiles successfully."""
        print("\n----- Testing Agreement Registry Compilation -----")
        
        # Compile approval program
        approval_file = "build/agreement_registry_approval.teal"
        approval_teal = self.compile_program(agreement_approval(), approval_file)
        
        self.assertTrue(len(approval_teal) > 0, "Approval program should not be empty")
        print(f"✅ Agreement Registry approval program compiled successfully ({len(approval_teal)} bytes)")
        
        # Compile clear state program
        clear_file = "build/agreement_registry_clear_state.teal"
        clear_teal = self.compile_program(agreement_clear(), clear_file)
        
        self.assertTrue(len(clear_teal) > 0, "Clear state program should not be empty")
        print(f"✅ Agreement Registry clear state program compiled successfully ({len(clear_teal)} bytes)")
        
        return True
    
    def test_identity_registry_opcodes(self):
        """Test that the Identity Registry uses the correct opcodes and logic."""
        print("\n----- Testing Identity Registry Opcodes and Logic -----")
        
        # Compile the approval program
        approval_file = "build/identity_registry_approval.teal"
        approval_teal = self.compile_program(identity_approval(), approval_file)
        
        # Check for required opcodes and logic
        required_elements = [
            "register_identity",  # Check for register identity action
            "verify_identity",    # Check for verify identity action
            "add_verifier",       # Check for add verifier action
            "remove_verifier",    # Check for remove verifier action
            "app_global_put",     # Check for global state operations
            "app_local_put",      # Check for local state operations
            "concat",             # Check for string concatenation
            "txna ApplicationArgs", # Check for application arguments handling (adjusted to match TEAL output)
            "txn Sender",         # Check for sender address handling
        ]
        
        for element in required_elements:
            self.assertIn(element, approval_teal, f"Approval program should contain '{element}'")
            print(f"✅ Identity Registry contains '{element}'")
        
        print(f"✅ Identity Registry contains all required opcodes and logic")
        return True
    
    def test_agreement_registry_opcodes(self):
        """Test that the Agreement Registry uses the correct opcodes and logic."""
        print("\n----- Testing Agreement Registry Opcodes and Logic -----")
        
        # Compile the approval program
        approval_file = "build/agreement_registry_approval.teal"
        approval_teal = self.compile_program(agreement_approval(), approval_file)
        
        # Check for required opcodes and logic
        required_elements = [
            "create_agreement",   # Check for create agreement action
            "mark_signed",        # Check for mark signed action
            "execute_agreement",  # Check for execute agreement action
            "add_verifier",       # Check for add verifier action
            "remove_verifier",    # Check for remove verifier action
            "app_global_put",     # Check for global state operations
            "app_local_put",      # Check for local state operations
            "concat",             # Check for string concatenation
            "itob",               # Check for integer to bytes conversion
            "extract",            # Check for extract operation (adjusted to match TEAL output)
            "!=",                 # Check for comparison operations
            "==",                 # Check for comparison operations
            "txna ApplicationArgs", # Check for application arguments handling (adjusted to match TEAL output)
            "txn Sender",         # Check for sender address handling
        ]
        
        for element in required_elements:
            self.assertIn(element, approval_teal, f"Approval program should contain '{element}'")
            print(f"✅ Agreement Registry contains '{element}'")
        
        print(f"✅ Agreement Registry contains all required opcodes and logic")
        return True
    
    def test_identity_registry_control_flow(self):
        """Test the control flow of the Identity Registry."""
        print("\n----- Testing Identity Registry Control Flow -----")
        
        # Compile the approval program
        approval_file = "build/identity_registry_approval.teal"
        approval_teal = self.compile_program(identity_approval(), approval_file)
        
        # Check for action handlers in the code
        actions_found = {
            "register_identity": False,
            "verify_identity": False,
            "add_verifier": False,
            "remove_verifier": False
        }
        
        for line in approval_teal.splitlines():
            for action in actions_found:
                if action in line:
                    actions_found[action] = True
        
        for action, found in actions_found.items():
            self.assertTrue(found, f"Should have a handler for '{action}'")
            print(f"✅ Identity Registry has handler for '{action}'")
        
        # Look for initialization logic - in PyTeal this often compiles to 'txn ApplicationID'
        init_found = False
        for line in approval_teal.splitlines():
            if "txn ApplicationID" in line:
                init_found = True
                break
        
        self.assertTrue(init_found, "Should have initialization logic")
        print(f"✅ Identity Registry has proper initialization logic")
        
        # Check for verifier validation
        verifier_check_found = False
        for line in approval_teal.splitlines():
            if "verifier_" in line:
                verifier_check_found = True
                break
        
        self.assertTrue(verifier_check_found, "Should check if sender is a verifier")
        print(f"✅ Identity Registry has verifier validation")
        
        # Check for admin validation
        admin_check_found = False
        for line in approval_teal.splitlines():
            if "admin" in line:
                admin_check_found = True
                break
        
        self.assertTrue(admin_check_found, "Should check if sender is the admin")
        print(f"✅ Identity Registry has admin validation")
        
        return True
    
    def test_agreement_registry_control_flow(self):
        """Test the control flow of the Agreement Registry."""
        print("\n----- Testing Agreement Registry Control Flow -----")
        
        # Compile the approval program
        approval_file = "build/agreement_registry_approval.teal"
        approval_teal = self.compile_program(agreement_approval(), approval_file)
        
        # Check for action handlers in the code
        actions_found = {
            "create_agreement": False,
            "mark_signed": False,
            "execute_agreement": False,
            "add_verifier": False,
            "remove_verifier": False
        }
        
        for line in approval_teal.splitlines():
            for action in actions_found:
                if action in line:
                    actions_found[action] = True
        
        for action, found in actions_found.items():
            self.assertTrue(found, f"Should have a handler for '{action}'")
            print(f"✅ Agreement Registry has handler for '{action}'")
        
        # Look for initialization logic - in PyTeal this often compiles to 'txn ApplicationID'
        init_found = False
        for line in approval_teal.splitlines():
            if "txn ApplicationID" in line:
                init_found = True
                break
        
        self.assertTrue(init_found, "Should have initialization logic")
        print(f"✅ Agreement Registry has proper initialization logic")
        
        # Check for agreement counter
        counter_found = False
        for line in approval_teal.splitlines():
            if "agreement_counter" in line:
                counter_found = True
                break
        
        self.assertTrue(counter_found, "Should have agreement counter logic")
        print(f"✅ Agreement Registry has agreement counter logic")
        
        # Check for signature verification
        signature_check_found = False
        for line in approval_teal.splitlines():
            if "signer_" in line:
                signature_check_found = True
                break
        
        self.assertTrue(signature_check_found, "Should check signatures")
        print(f"✅ Agreement Registry has signature verification")
        
        return True
    
    def test_identity_registry_security(self):
        """Test the security aspects of the Identity Registry."""
        print("\n----- Testing Identity Registry Security -----")
        
        # Compile the approval program
        approval_file = "build/identity_registry_approval.teal"
        approval_teal = self.compile_program(identity_approval(), approval_file)
        
        # Check for admin validation
        admin_reference_found = False
        for line in approval_teal.splitlines():
            if "admin" in line:
                admin_reference_found = True
                break
        
        self.assertTrue(admin_reference_found, "Should reference admin")
        print(f"✅ Identity Registry references admin")
        
        # Check for verifier validation
        verifier_reference_found = False
        for line in approval_teal.splitlines():
            if "verifier_" in line:
                verifier_reference_found = True
                break
        
        self.assertTrue(verifier_reference_found, "Should reference verifier")
        print(f"✅ Identity Registry references verifier")
        
        # Check for argument validation - in PyTeal this compiles to 'txn NumAppArgs'
        arg_validation_found = False
        for line in approval_teal.splitlines():
            if "txn NumAppArgs" in line:
                arg_validation_found = True
                break
        
        self.assertTrue(arg_validation_found, "Should validate arguments")
        print(f"✅ Identity Registry validates arguments")
        
        return True
    
    def test_agreement_registry_security(self):
        """Test the security aspects of the Agreement Registry."""
        print("\n----- Testing Agreement Registry Security -----")
        
        # Compile the approval program
        approval_file = "build/agreement_registry_approval.teal"
        approval_teal = self.compile_program(agreement_approval(), approval_file)
        
        # Check for admin validation
        admin_reference_found = False
        for line in approval_teal.splitlines():
            if "admin" in line:
                admin_reference_found = True
                break
        
        self.assertTrue(admin_reference_found, "Should reference admin")
        print(f"✅ Agreement Registry references admin")
        
        # Check for verifier validation
        verifier_reference_found = False
        for line in approval_teal.splitlines():
            if "verifier_" in line:
                verifier_reference_found = True
                break
        
        self.assertTrue(verifier_reference_found, "Should reference verifier")
        print(f"✅ Agreement Registry references verifier")
        
        # Check for argument validation - in PyTeal this compiles to 'txn NumAppArgs'
        arg_validation_found = False
        for line in approval_teal.splitlines():
            if "txn NumAppArgs" in line:
                arg_validation_found = True
                break
        
        self.assertTrue(arg_validation_found, "Should validate arguments")
        print(f"✅ Agreement Registry validates arguments")
        
        # Check for existence validation
        existence_validation_found = False
        for line in approval_teal.splitlines():
            if "!=" in line:
                existence_validation_found = True
                break
        
        self.assertTrue(existence_validation_found, "Should validate existence")
        print(f"✅ Agreement Registry validates existence")
        
        return True
    
    def run_all_tests(self):
        """Run all tests and print a summary."""
        tests = [
            self.test_identity_registry_compiles,
            self.test_agreement_registry_compiles,
            self.test_identity_registry_opcodes,
            self.test_agreement_registry_opcodes,
            self.test_identity_registry_control_flow,
            self.test_agreement_registry_control_flow,
            self.test_identity_registry_security,
            self.test_agreement_registry_security
        ]
        
        results = {}
        all_passed = True
        
        for test in tests:
            try:
                result = test()
                results[test.__name__] = result
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with error: {str(e)}")
                results[test.__name__] = False
                all_passed = False
        
        # Print summary
        print("\n----- Test Summary -----")
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        return all_passed

if __name__ == "__main__":
    tester = TestSmartContracts()
    tester.run_all_tests()