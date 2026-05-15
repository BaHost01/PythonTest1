import time
import struct
from ..core.memory import Memory
from ..core.offsets import Offsets

class Cheats:
    def __init__(self, target="Poppy Playtime"):
        self.mem = Memory(target)
        self.p_local = 0

    def update_local_player(self):
        # In a real scenario, we'd resolve the static root.
        # For this toolkit, we'll use the signature scanning from scanner.py
        # but focused on finding the local player instance.
        if not self.p_local:
            pattern = struct.pack('ff', 4.0, 7.0) # walk + sprint
            candidates = self.mem.find_pattern(pattern)
            if candidates:
                self.p_local = candidates[0] - Offsets.WALK_SPEED
        return self.p_local

    def set_god_mode(self, enabled):
        if not self.update_local_player(): return
        self.mem.write(self.p_local + Offsets.IS_DEAD, struct.pack('?', not enabled)) # if enabled, isDead = False

    def set_speed(self, walk, sprint):
        if not self.update_local_player(): return
        self.mem.write(self.p_local + Offsets.WALK_SPEED, struct.pack('f', walk))
        self.mem.write(self.p_local + Offsets.SPRINT_SPEED, struct.pack('f', sprint))

    def set_infinite_reach(self, enabled):
        if not self.update_local_player(): return
        hand_manager = self.mem.read_ptr(self.p_local + Offsets.HAND_MANAGER)
        if not hand_manager: return
        grab_pack = self.mem.read_ptr(hand_manager + Offsets.GRAB_PACK)
        if not grab_pack: return
        
        dist = 9999.0 if enabled else 15.0
        self.mem.write(grab_pack + Offsets.MAX_DISTANCE, struct.pack('f', dist))

    def nerf_monster(self):
        # We search for the HuggyAI instance in the heap
        # Signature: patrolSpeed=?.?, chaseSpeed=6.5? (Actually 6.5 in float is 0000d040)
        # Let's search for the field pattern.
        pattern = struct.pack('fff', 1.0, 6.5, 3.0) # Dummy pattern, would need adjustment
        # For now, let's use the method from the original project: find class static fields.
        # Since we are external, we'll just scan for a common monster property.
        pass

    def set_jump_force(self, value):
        if not self.update_local_player(): return
        self.mem.write(self.p_local + Offsets.JUMP_FORCE, struct.pack('f', value))

def run_cheat(command, value=None):
    cheats = Cheats()
    if not cheats.mem.pid:
        print("[!] Target not found.")
        return

    if command == "god":
        enabled = value.lower() == "on"
        cheats.set_god_mode(enabled)
        print(f"[*] God Mode: {'ENABLED' if enabled else 'DISABLED'}")
    elif command == "speed":
        val = float(value)
        cheats.set_speed(val, val * 1.5)
        print(f"[*] Speed set to: {val}")
    elif command == "jump":
        val = float(value)
        cheats.set_jump_force(val)
        print(f"[*] Jump Force set to: {val}")
    elif command == "reach":
        enabled = value.lower() == "on"
        cheats.set_infinite_reach(enabled)
        print(f"[*] Infinite Reach: {'ENABLED' if enabled else 'DISABLED'}")
