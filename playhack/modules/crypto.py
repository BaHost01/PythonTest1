import re
import argparse
from ..core.memory import Memory

class Crypto:
    MAGIC = 0xDEADBEEFCAFEBABE

    def __init__(self, width=64):
        self.width = width
        self.mask = (1 << width) - 1

    def rol(self, value, bits):
        return ((value << bits) | (value >> (self.width - bits))) & self.mask

    def ror(self, value, bits):
        return ((value >> bits) | (value << (self.width - bits))) & self.mask

    def encrypt(self, value, k1, k2):
        x = value & self.mask
        x ^= self.MAGIC & self.mask
        x = (x + k2) & self.mask
        x = self.rol(x, 13)
        x ^= k1
        return x

    def decrypt(self, value, k1, k2):
        x = value & self.mask
        x ^= k1
        x = self.ror(x, 13)
        x = (x - k2) & self.mask
        x ^= self.MAGIC & self.mask
        return x

def run_patch(input_file, output_file, k1, k2):
    crypto = Crypto()
    with open(input_file, 'r') as f:
        content = f.read()
    
    def replace_hex(match):
        val = int(match.group(0), 16)
        enc = crypto.encrypt(val, k1, k2)
        return f"DECRYPT_OFFSET(0x{enc:X})"

    new_content = re.sub(r"0x[a-fA-F0-9]+", replace_hex, content)
    out = output_file or input_file + ".patched"
    with open(out, 'w') as f:
        f.write(new_content)
    print(f"[*] Patched {input_file} -> {out}")
