import os
import struct
import re
import platform
import ctypes
from ctypes import wintypes

class Memory:
    def __init__(self, process_name=None, pid=None):
        self.os = platform.system()
        self.pid = pid if pid else self._find_pid(process_name)
        self.handle = None
        
        if self.pid:
            if self.os == "Windows":
                # PROCESS_ALL_ACCESS = 0x1F0FFF
                self.handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, self.pid)
            else:
                try:
                    self.handle = open(f"/proc/{self.pid}/mem", "rb+")
                except PermissionError:
                    print(f"[!] Permission denied to access PID {self.pid}")

    def _find_pid(self, name):
        if self.os == "Windows":
            import ctypes.wintypes
            # Simplified Windows PID finding
            SNAPPROCESS = 0x00000002
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [("dwSize", wintypes.DWORD),
                            ("cntUsage", wintypes.DWORD),
                            ("th32ProcessID", wintypes.DWORD),
                            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                            ("th32ModuleID", wintypes.DWORD),
                            ("cntThreads", wintypes.DWORD),
                            ("th32ParentProcessID", wintypes.DWORD),
                            ("pcPriClassBase", wintypes.LONG),
                            ("dwFlags", wintypes.DWORD),
                            ("szExeFile", ctypes.c_char * 260)]
            
            hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(SNAPPROCESS, 0)
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
            if ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
                while True:
                    if name.lower() in pe.szExeFile.decode().lower():
                        ctypes.windll.kernel32.CloseHandle(hSnapshot)
                        return pe.th32ProcessID
                    if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                        break
            ctypes.windll.kernel32.CloseHandle(hSnapshot)
            return None
        else:
            try:
                output = os.popen(f"pgrep -f '{name}'").read().strip()
                return int(output.split('\n')[0]) if output else None
            except: return None

    def read(self, address, size):
        if not self.handle: return None
        if self.os == "Windows":
            buffer = ctypes.create_string_buffer(size)
            bytes_read = wintypes.SIZE_T()
            if ctypes.windll.kernel32.ReadProcessMemory(self.handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytes_read)):
                return buffer.raw
            return None
        else:
            try:
                self.handle.seek(address)
                return self.handle.read(size)
            except: return None

    def write(self, address, data):
        if not self.handle: return False
        if self.os == "Windows":
            bytes_written = wintypes.SIZE_T()
            return bool(ctypes.windll.kernel32.WriteProcessMemory(self.handle, ctypes.c_void_p(address), data, len(data), ctypes.byref(bytes_written)))
        else:
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
        if self.os == "Windows":
            # Simplified Windows module mapping
            # This would normally use EnumProcessModules
            pass
        else:
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
        # Pattern scanning on Windows would require VirtualQueryEx for performance
        # For now, we'll keep the Linux /proc scanner
        if self.os != "Windows":
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
