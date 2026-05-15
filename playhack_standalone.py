#!/usr/bin/env python3
import os
import struct
import re
import platform
import ctypes
import sys
import time
import argparse
import json
import binascii
from ctypes import wintypes

# --- Core: Offsets ---
class Offsets:
    LOCAL_INSTANCE = 0x0400027f 
    WALK_SPEED = 0x283
    SPRINT_SPEED = 0x284
    JUMP_FORCE = 0x285
    IS_DEAD = 0x2D9
    HAND_MANAGER = 0x250
    GRAB_PACK = 0x20
    MAX_DISTANCE = 0x107
    HUGGY_CHASE_SPEED = 0x176
    HUGGY_VISION_RANGE = 0x178
    TRANSFORM = 0x50
    POS_X = 0x90
    POS_Y = 0x94
    POS_Z = 0x98

# --- Core: Memory ---
class Memory:
    def __init__(self, process_name=None, pid=None):
        self.os = platform.system()
        self.pid = pid if pid else self._find_pid(process_name)
        self.handle = None
        if self.pid:
            if self.os == "Windows":
                self.handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, self.pid)
            else:
                try: self.handle = open(f"/proc/{self.pid}/mem", "rb+")
                except: pass

    def _find_pid(self, name):
        if self.os == "Windows":
            SNAPPROCESS = 0x00000002
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)), ("th32ModuleID", wintypes.DWORD),
                            ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                            ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_char * 260)]
            hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(SNAPPROCESS, 0)
            pe = PROCESSENTRY32(); pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
            if ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
                while True:
                    if name.lower() in pe.szExeFile.decode().lower():
                        ctypes.windll.kernel32.CloseHandle(hSnapshot); return pe.th32ProcessID
                    if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)): break
            ctypes.windll.kernel32.CloseHandle(hSnapshot); return None
        else:
            try:
                output = os.popen(f"pgrep -f '{name}'").read().strip()
                return int(output.split('\n')[0]) if output else None
            except: return None

    def read(self, address, size):
        if not self.handle: return None
        if self.os == "Windows":
            buffer = ctypes.create_string_buffer(size); bytes_read = wintypes.SIZE_T()
            if ctypes.windll.kernel32.ReadProcessMemory(self.handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytes_read)):
                return buffer.raw
            return None
        else:
            try: self.handle.seek(address); return self.handle.read(size)
            except: return None

    def write(self, address, data):
        if not self.handle: return False
        if self.os == "Windows":
            bytes_written = wintypes.SIZE_T()
            return bool(ctypes.windll.kernel32.WriteProcessMemory(self.handle, ctypes.c_void_p(address), data, len(data), ctypes.byref(bytes_written)))
        else:
            try: self.handle.seek(address); self.handle.write(data); return True
            except: return False

    def read_float(self, address):
        data = self.read(address, 4)
        return struct.unpack('f', data)[0] if data else 0.0

    def read_ptr(self, address):
        data = self.read(address, 8)
        return struct.unpack('Q', data)[0] if data else 0

    def find_pattern(self, pattern, perms="rw-p"):
        results = []
        if self.os != "Windows":
            try:
                with open(f"/proc/{self.pid}/maps", "r") as f:
                    for line in f:
                        if perms not in line: continue
                        parts = line.split()
                        start, end = [int(x, 16) for x in parts[0].split('-')]
                        self.handle.seek(start)
                        chunk = self.handle.read(end - start)
                        idx = chunk.find(pattern)
                        while idx != -1:
                            results.append(start + idx)
                            idx = chunk.find(pattern, idx + 1)
            except: pass
        return results

# --- Module: Cheats ---
class Cheats:
    def __init__(self, mem):
        self.mem = mem; self.p_local = 0
    def update_local(self):
        if not self.p_local:
            pattern = struct.pack('ff', 4.0, 7.0)
            candidates = self.mem.find_pattern(pattern)
            if candidates: self.p_local = candidates[0] - Offsets.WALK_SPEED
        return self.p_local
    def god(self, enabled):
        if self.update_local(): self.mem.write(self.p_local + Offsets.IS_DEAD, struct.pack('?', not enabled))
    def speed(self, val):
        if self.update_local():
            self.mem.write(self.p_local + Offsets.WALK_SPEED, struct.pack('f', val))
            self.mem.write(self.p_local + Offsets.SPRINT_SPEED, struct.pack('f', val * 1.5))
    def jump(self, val):
        if self.update_local(): self.mem.write(self.p_local + Offsets.JUMP_FORCE, struct.pack('f', val))
    def reach(self, enabled):
        if self.update_local():
            hm = self.mem.read_ptr(self.p_local + Offsets.HAND_MANAGER)
            if hm:
                gp = self.mem.read_ptr(hm + Offsets.GRAB_PACK)
                if gp: self.mem.write(gp + Offsets.MAX_DISTANCE, struct.pack('f', 9999.0 if enabled else 15.0))

# --- Module: ESP (Simplified for Standalone) ---
def run_esp(target):
    from rich.live import Live
    from rich.table import Table
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    
    console = Console()
    mem = Memory(target)
    cheats = Cheats(mem)
    
    def generate_radar(data):
        size = 15; grid = [[" " for _ in range(size)] for _ in range(size)]; center = size // 2
        grid[center][center] = "[blue]@[/blue]"
        if len(data) > 1:
            local = data[0]; scale = 5.0
            for p in data[1:]:
                gx = int(center + (p['x'] - local['x']) / scale)
                gz = int(center - (p['z'] - local['z']) / scale)
                if 0 <= gx < size and 0 <= gz < size: grid[gz][gx] = "[red]X[/red]"
        return Panel("\n".join([" ".join(row) for row in grid]), title="Radar")

    def get_data():
        players = []
        # Pattern scan for demo/fallback
        pattern = struct.pack('ff', 4.0, 7.0)
        candidates = mem.find_pattern(pattern)
        for c in candidates:
            addr = c - Offsets.WALK_SPEED
            is_dead = struct.unpack('?', mem.read(addr + Offsets.IS_DEAD, 1))[0] if mem.read(addr + Offsets.IS_DEAD, 1) else True
            tp = mem.read_ptr(addr + Offsets.TRANSFORM)
            x = mem.read_float(tp + Offsets.POS_X); y = mem.read_float(tp + Offsets.POS_Y); z = mem.read_float(tp + Offsets.POS_Z)
            players.append({"state": "[red]DEAD[/red]" if is_dead else "[green]ALIVE[/green]", "x": x, "y": y, "z": z, "pos": f"({x:.1f}, {y:.1f}, {z:.1f})"})
        return players

    layout = Layout()
    layout.split_column(Layout(name="main"), Layout(name="status", size=3))
    
    with Live(layout, refresh_per_second=10) as live:
        while True:
            data = get_data()
            table = Table(title="Players")
            table.add_column("State"); table.add_column("Position")
            for p in data: table.add_row(p['state'], p['pos'])
            layout["main"].update(Panel(table))
            layout["status"].update(Panel(f"Target: {target} | PID: {mem.pid}"))
            time.sleep(0.1)

# --- CLI Entry Point ---
def main():
    parser = argparse.ArgumentParser(description="PlayHack Standalone")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("esp")
    god = subparsers.add_parser("god"); god.add_argument("state", choices=["on", "off"])
    speed = subparsers.add_parser("speed"); speed.add_argument("value", type=float)
    jump = subparsers.add_parser("jump"); jump.add_argument("value", type=float)
    reach = subparsers.add_parser("reach"); reach.add_argument("state", choices=["on", "off"])
    
    args = parser.parse_args()
    mem = Memory("Poppy Playtime")
    cheats = Cheats(mem)

    if args.command == "esp": run_esp("Poppy Playtime")
    elif args.command == "god": cheats.god(args.state == "on")
    elif args.command == "speed": cheats.speed(args.value)
    elif args.command == "jump": cheats.jump(args.value)
    elif args.command == "reach": cheats.reach(args.state == "on")
    else: parser.print_help()

if __name__ == "__main__":
    main()
