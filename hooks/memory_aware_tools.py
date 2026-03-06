#!/usr/bin/env python3
"""
Memory-Aware Tools for Immediate Testing

Purpose: Provide wrapped versions of tools that I (Black Roger) can use immediately
This is a workaround until proper OpenClaw skill integration
"""

import os
import sys

# Kill switch
MEMORY_CONTRACT_ENABLED = os.getenv('MEMORY_CONTRACT_ENABLED', 'true')
if MEMORY_CONTRACT_ENABLED.lower() == 'false':
    print("[Memory Contract] DISABLED - using original tools")
    # In this case, we would just pass through to original tools
    # For now, we'll still demonstrate the concept

# Import OpenClaw tools (as they're available to the agent)
# Note: In actual OpenClaw agent context, these would be available
try:
    # Try to import the tools that OpenClaw provides to agents
    # This is what would work inside OpenClaw
    print("[Memory Contract] Attempting to import OpenClaw tools...")
    
    # In real OpenClaw, tools are injected into agent context
    # For demonstration, we'll create mock versions
    
    def mock_exec(**kwargs):
        """Mock exec tool for demonstration"""
        print(f"[Mock Exec] Command: {kwargs.get('command', '')}")
        return {"status": "success", "output": "Mock output"}
    
    def mock_write(**kwargs):
        """Mock write tool for demonstration"""
        print(f"[Mock Write] Path: {kwargs.get('path', '')}")
        return {"status": "success"}
    
    # Store the original tools
    original_tools = {
        'exec': mock_exec,
        'write': mock_write,
        'edit': None,  # Would be actual OpenClaw tools in production
        'browser': None,
        'message': None
    }
    
    print("[Memory Contract] Created mock tools for demonstration")
    
except Exception as e:
    print(f"[Memory Contract ERROR] Could not access tools: {e}")
    original_tools = {}

# Import our memory contract hooks
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from pre_action_memory import pre_action_memory_search
    from post_decision_memory import post_decision_memory_persistence
    
    print("[Memory Contract] Hooks loaded successfully")
except ImportError as e:
    print(f"[Memory Contract ERROR] Could not load hooks: {e}")
    # Create fallback functions
    def pre_action_memory_search(context):
        print(f"[Memory Contract] Pre-action search (fallback): {context.get('tool')}")
        return None
    
    def post_decision_memory_persistence(decision, outcome, metadata):
        print(f"[Memory Contract] Post-decision write (fallback): {decision[:50]}...")
        return {"status": "fallback"}

def memory_aware_exec(**kwargs):
    """Memory-aware version of exec tool"""
    if MEMORY_CONTRACT_ENABLED.lower() != 'true':
        # Pass through to original
        return original_tools['exec'](**kwargs)
    
    # Pre-action search
    context = {
        "tool": "exec",
        "command": kwargs.get('command', ''),
        "timestamp": "2026-03-06T16:00:00Z",
        "user_request": "User requested command execution"
    }
    
    print("[Memory Contract] Pre-action search for exec...")
    memory_results = pre_action_memory_search(context)
    
    # Execute
    print(f"[Memory Contract] Executing command...")
    result = original_tools['exec'](**kwargs)
    
    # Post-decision persistence
    decision = f"Executed: {kwargs.get('command', '')[:100]}"
    outcome = f"Result: {result.get('status', 'unknown')}"
    metadata = {
        "tool": "exec",
        "command": kwargs.get('command', ''),
        "result": result.get('status', ''),
        "context": "Command execution",
        "tags": ["exec", "command"]
    }
    
    print("[Memory Contract] Post-decision write...")
    write_result = post_decision_memory_persistence(decision, outcome, metadata)
    
    return result

def memory_aware_write(**kwargs):
    """Memory-aware version of write tool"""
    if MEMORY_CONTRACT_ENABLED.lower() != 'true':
        return original_tools['write'](**kwargs)
    
    # Pre-action search
    context = {
        "tool": "write",
        "path": kwargs.get('path', ''),
        "timestamp": "2026-03-06T16:00:00Z"
    }
    
    print("[Memory Contract] Pre-action search for write...")
    memory_results = pre_action_memory_search(context)
    
    # Execute
    print(f"[Memory Contract] Writing file...")
    result = original_tools['write'](**kwargs)
    
    # Post-decision persistence
    decision = f"Wrote to: {kwargs.get('path', '')}"
    outcome = f"Success: {result.get('status', 'unknown')}"
    metadata = {
        "tool": "write",
        "path": kwargs.get('path', ''),
        "content_length": len(kwargs.get('content', '')),
        "context": "File write",
        "tags": ["write", "file"]
    }
    
    print("[Memory Contract] Post-decision write...")
    write_result = post_decision_memory_persistence(decision, outcome, metadata)
    
    return result

def test_memory_aware_tools():
    """Test the memory-aware tools"""
    print("\n" + "="*60)
    print("Testing Memory-Aware Tools")
    print("="*60)
    
    print("\nTest 1: memory_aware_exec")
    print("-" * 40)
    result = memory_aware_exec(command="ls -la", workdir="/tmp")
    print(f"Result: {result}")
    
    print("\nTest 2: memory_aware_write")
    print("-" * 40)
    result = memory_aware_write(
        path="/tmp/test_memory_contract.txt",
        content="Test content for memory contract"
    )
    print(f"Result: {result}")
    
    print("\nTest 3: Check logs")
    print("-" * 40)
    log_files = [
        config.get('search_log'),
        config.get('write_log')
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"{os.path.basename(log_file)}: {len(lines)} entries")
        else:
            print(f"{os.path.basename(log_file)}: not found")
    
    print("\n" + "="*60)
    print("✅ Memory-Aware Tools Test Complete")
    print("="*60)

# Usage instructions
def show_usage():
    print("\n" + "="*60)
    print("Memory-Aware Tools Usage")
    print("="*60)
    print("\nIn your agent code, replace:")
    print("  exec(command='ls -la')")
    print("with:")
    print("  memory_aware_exec(command='ls -la')")
    print("\nThe memory-aware version will:")
    print("  1. Search memory before execution")
    print("  2. Execute the command")
    print("  3. Write decision to memory")
    print("  4. Track compliance metrics")
    print("\nAvailable tools:")
    print("  - memory_aware_exec()")
    print("  - memory_aware_write()")
    print("  - (more to be added)")
    print("\nKill Switch: Set MEMORY_CONTRACT_ENABLED=false")

# Main execution
if __name__ == "__main__":
    print("[Memory Contract] Memory-Aware Tools Module")
    
    if MEMORY_CONTRACT_ENABLED.lower() != 'true':
        print("  DISABLED via environment variable")
        print("  Tools will pass through to originals")
    
    show_usage()
    
    # Run test if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_memory_aware_tools()
    elif len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_usage()
    else:
        print("\nRun with --test to test the tools")
        print("Run with --help to show usage")
from config_loader import get_config
config = get_config()