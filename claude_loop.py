#!/usr/bin/env python3
import subprocess
import time
import sys

def run_claude_loop(start_issue=43, end_issue=59, delay=5):
    """
    Execute the 'claude' command in a loop, waiting for each command to fully complete
    before starting the next one.
    
    Args:
        delay (int): Seconds to wait between command executions (after completion)
    """
    print(f"Starting claude command loop with {delay}s delay between completions...")
    print("Press Ctrl+C to stop")
    
    try:
        i=start_issue
        while i<=end_issue:

            code_user_story = f'backend-develop {i}'
            # plan_user_story = f'user-story-to-tech-plan {i}'
            command_issue = code_user_story
            
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting 'claude' command...")
            start_time = time.time()
            print(f"Command: /{command_issue}")
            try:
                # Use subprocess.run without timeout to let command complete naturally
                result = subprocess.run([f'claude -p --dangerously-skip-permissions "/{command_issue}"'], 
                                      capture_output=True, 
                                      text=True, shell=True)
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Command completed")
                print(f"Exit code: {result.returncode}")
                print(f"Duration: {duration:.2f} seconds")
                
                if result.stdout:
                    print(f"Output: {result.stdout}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                    
            except FileNotFoundError:
                print("Error: 'claude' command not found")
                break
            except Exception as e:
                print(f"Error executing command: {e}")
            
            i+=1
            print(f"Waiting {delay} seconds before next execution...")
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\nLoop stopped by user")

import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python claude_loop.py <start_issue>")
        sys.exit(1)
    try:
        start_issue = int(sys.argv[1])
    except ValueError:
        print("Error: <start_issue> must be an integer")
        sys.exit(1)
    run_claude_loop(start_issue=start_issue, end_issue=155, delay=500)