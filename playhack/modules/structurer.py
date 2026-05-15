import re
import json

class Structurer:
    def __init__(self):
        self.offsets = []

    def parse(self, text):
        lines = text.splitlines()
        for line in lines:
            line = line.replace('`', '').replace('\\', '').strip()
            line = re.sub(r'^[\s\-\*\+]+', '', line)

            # Simple Pattern (Name = Offset)
            m = re.search(r"([\w/]+)\s*[=:]\s*(0x[a-fA-F0-9]+)", line)
            if m:
                self.offsets.append({"name": m.group(1).replace('/', '_'), "offset": m.group(2)})
                continue

            # Index Pattern (Name (Field 123))
            m = re.search(r"([\w/]+)\s*\(Field\s+(\w+)\)", line)
            if m:
                self.offsets.append({"name": m.group(1).replace('/', '_'), "offset": m.group(2)})

    def to_cpp(self):
        output = ["#pragma once", "namespace Offsets {"]
        for o in self.offsets:
            output.append(f"    constexpr uintptr_t {o['name']} = {o['offset']};")
        output.append("}")
        return "\n".join(output)

def run_structure(input_file, output_file, format):
    s = Structurer()
    with open(input_file, 'r') as f:
        s.parse(f.read())
    
    if format == "cpp":
        res = s.to_cpp()
    else:
        res = json.dumps(s.offsets, indent=4)
        
    if output_file:
        with open(output_file, 'w') as f:
            f.write(res)
    else:
        print(res)
