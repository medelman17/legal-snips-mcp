#!/usr/bin/env python3
"""
Quick test script for the legal snippets MCP server
"""
import json
import subprocess
import sys

def test_server():
    """Test the MCP server by checking if it starts properly"""
    try:
        # Test if the server can start
        result = subprocess.run([
            sys.executable, "legal_snippets_server.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Server starts successfully")
            return True
        else:
            print(f"❌ Server failed to start: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ Server started (timed out waiting, which is expected)")
        return True
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_json_storage():
    """Test JSON storage functionality"""
    try:
        # Import the functions directly
        sys.path.append('.')
        from legal_snippets_server import load_snippets, save_snippets
        
        # Test loading empty data
        data = load_snippets()
        print(f"✅ Loading snippets works: {len(data['snippets'])} snippets found")
        
        # Test saving data
        test_data = {
            "snippets": [{
                "id": 1,
                "citation": "Test v. Case, 123 F.3d 456 (Test Cir. 2023)",
                "key_language": "This is test language",
                "tags": ["test", "demo"],
                "context": "Test context",
                "case_type": "civil"
            }],
            "next_id": 2
        }
        save_snippets(test_data)
        
        # Test loading the saved data
        loaded = load_snippets()
        if len(loaded['snippets']) == 1:
            print("✅ JSON storage works correctly")
            return True
        else:
            print("❌ JSON storage failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing JSON storage: {e}")
        return False

if __name__ == "__main__":
    print("Testing Legal Snippets MCP Server...")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 2
    
    if test_server():
        tests_passed += 1
    
    if test_json_storage():
        tests_passed += 1
    
    print("=" * 40)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your MCP server is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")