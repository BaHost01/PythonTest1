import os
import struct
import re

class Memory:
    def __init__(self, process_name=None, pid=None):
        self.pid = pid if pid else self._find_pid(process_name)
        self.handle = None
        if self.pid:
            try:
                self.handle = open(f"/proc/{self.pid}/mem", "rb+")
            except PermissionError:
                print(f"[!] Permission denied to access PID {self.pid}")

    def _find_pid(self, name):
        try:
            output = os.popen(f"pgrep -f '{name}'").read().strip()
            return int(output.split('\n')[0]) if output else None
        except: return None

    def read(self, address, size):
        if not self.handle: return None
        try:
            self.handle.seek(address)
            return self.handle.read(size)
        except: return None

    def write(self, address, data):
        if not self.handle: return False
        try:
            self.handle.seek(address)
            self.handle.write(data)
            return True
        except: return False

    def read_float(self, address):
        data = self.read(address, 4)
        return struct.unpack('f', data)[0] if data else 0.0

    def read_ptr(self, address):
        data = self.read(address, 8) # 64-bit
        return struct.unpack('Q', data)[0] if data else 0

    def read_chain(self, base, offsets):
        addr = base
        for i, offset in enumerate(offsets):
            addr = self.read_ptr(addr)
            if not addr: return 0
            if i < len(offsets) - 1:
                addr += offset
        return addr + offsets[-1] if offsets else addr

    def get_maps(self, filter_name=None):
        maps = []
        try:
            with open(f"/proc/{self.pid}/maps", "r") as f:
                for line in f:
                    if filter_name and filter_name not in line: continue
                    parts = line.split()
                    addr_range = parts[0].split('-')
                    maps.append({
                        'start': int(addr_range[0], 16),
                        'end': int(addr_range[1], 16),
                        'perms': parts[1],
                        'path': parts[-1] if len(parts) > 5 else ""
                    })
        except: pass
        return maps

    def find_pattern(self, pattern, perms="rw-p"):
        results = []
        for m in self.get_maps():
            if perms not in m['perms']: continue
            try:
                self.handle.seek(m['start'])
                chunk = self.handle.read(m['end'] - m['start'])
                idx = chunk.find(pattern)
                while idx != -1:
                    results.append(m['start'] + idx)
                    idx = chunk.find(pattern, idx + 1)
            except: continue
        return results
