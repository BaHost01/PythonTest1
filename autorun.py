#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def run_command(cmd):
    print(f"[*] Executing: {cmd}")
    return subprocess.run(cmd, shell=True)

def main():
    print("=== PlayHack Auto-Setup & Launch ===")
    
    # 1. Install dependencies
    print("[*] Checking dependencies...")
    run_command("pip install rich --quiet")
    
    # 2. Wait for game
    print("[*] Waiting for 'Poppy Playtime' process...")
    target = "Poppy Playtime"
    found = False
    for _ in range(10): # Try for 10 seconds
        output = os.popen(f"pgrep -f '{target}'").read().strip()
        if output:
            print(f"[+] Game found! (PID: {output.split()[0]})")
            found = True
            break
        time.sleep(1)
    
    if not found:
        print("[!] Game not found. Running in simulation mode.")
    
    # 3. Apply basic cheats automatically
    print("[*] Auto-applying God Mode and Infinite Reach...")
    run_command("python3 playhack.py god on")
    run_command("python3 playhack.py reach on")
    
    # 4. Launch ESP
    print("[*] Launching ESP Dashboard...")
    time.sleep(1)
    os.system("python3 playhack.py esp")

if __name__ == "__main__":
    main()
