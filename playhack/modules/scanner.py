import time
import struct
import binascii
from ..core.memory import Memory

def parse_pattern(pattern_str):
    pattern_bytes = []
    parts = pattern_str.split()
    for p in parts:
        if p == '?' or p == '??':
            pattern_bytes.append(None)
        else:
            pattern_bytes.append(int(p, 16))
    return pattern_bytes

def match_pattern(data, pattern):
    if len(data) < len(pattern): return False
    for i in range(len(pattern)):
        if pattern[i] is not None and data[i] != pattern[i]:
            return False
    return True

def run_scan(target, value=None, pattern=None, duration=10):
    mem = Memory(target)
    if not mem.pid:
        print(f"[!] Target {target} not found.")
        return

    if value is not None:
        print(f"[*] Initial scan for float: {value}")
        search_bytes = struct.pack('f', float(value))
        candidates = mem.find_pattern(search_bytes)
    elif pattern:
        print(f"[*] Initial scan for pattern: {pattern}")
        p_bytes = parse_pattern(pattern)
        # Simplified pattern search: use first non-wildcard byte to narrow down
        first_byte = next(b for b in p_bytes if b is not None)
        raw_candidates = mem.find_pattern(bytes([first_byte]))
        candidates = []
        for c in raw_candidates:
            data = mem.read(c, len(p_bytes))
            if data and match_pattern(data, p_bytes):
                candidates.append(c)
    
    print(f"[*] Found {len(candidates)} candidates. Filtering for {duration}s...")

    valid = set(candidates)
    start = time.time()
    try:
        while time.time() - start < duration:
            for addr in list(valid):
                if value is not None:
                    val = mem.read_float(addr)
                    if abs(val - float(value)) > 0.001:
                        valid.remove(addr)
                elif pattern:
                    data = mem.read(addr, len(p_bytes))
                    if not data or not match_pattern(data, p_bytes):
                        valid.remove(addr)
            
            print(f"[*] Active Candidates: {len(valid)}", end='\r')
            time.sleep(1)
    except KeyboardInterrupt: pass

    print(f"\n[*] Results saved to live_offsets.txt")
    with open("live_offsets.txt", "w") as f:
        for i, addr in enumerate(valid):
            f.write(f"Scan_Result_{i} = 0x{addr:X}\n")
