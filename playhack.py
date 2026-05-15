#!/usr/bin/env python3
import argparse
import sys
from playhack.modules import esp, scanner, crypto, structurer, cheats

def main():
    parser = argparse.ArgumentParser(description="PlayHack Unified Game Toolkit")
    subparsers = parser.add_subparsers(dest="command", help="Available modules")

    # ESP
    esp_p = subparsers.add_parser("esp", help="Run the ESP TUI")
    esp_p.add_argument("--target", default="Poppy Playtime", help="Target process name")

    # Scan
    scan_p = subparsers.add_parser("scan", help="Memory scanner")
    scan_p.add_argument("value", nargs="?", type=float, help="Float value to find")
    scan_p.add_argument("--pattern", help="Hex pattern (e.g., '48 8b 05')")
    scan_p.add_argument("--target", default="Poppy Playtime")
    scan_p.add_argument("--duration", type=int, default=10)

    # Cheats
    god_p = subparsers.add_parser("god", help="Toggle God Mode")
    god_p.add_argument("state", choices=["on", "off"])

    reach_p = subparsers.add_parser("reach", help="Toggle Infinite Reach")
    reach_p.add_argument("state", choices=["on", "off"])

    speed_p = subparsers.add_parser("speed", help="Set Player Speed")
    speed_p.add_argument("value", type=float)

    jump_p = subparsers.add_parser("jump", help="Set Jump Force")
    jump_p.add_argument("value", type=float)

    # Crypto
    cry_p = subparsers.add_parser("crypto", help="Offset obfuscation")
    cry_p.add_argument("input", help="Input file")
    cry_p.add_argument("-o", "--output")
    cry_p.add_argument("--key1", default="0x123456789ABCDEF0")
    cry_p.add_argument("--key2", default="0x1122334455667788")

    # Structure
    str_p = subparsers.add_parser("structure", help="Offset structurer")
    str_p.add_argument("input")
    str_p.add_argument("-o", "--output")
    str_p.add_argument("-f", "--format", choices=["cpp", "json"], default="cpp")

    args = parser.parse_args()

    if args.command == "esp":
        esp.run(args.target)
    elif args.command == "scan":
        scanner.run_scan(args.target, value=args.value, pattern=args.pattern, duration=args.duration)
    elif args.command in ["god", "reach", "speed"]:
        cheats.run_cheat(args.command, getattr(args, "state", getattr(args, "value", None)))
    elif args.command == "crypto":
        crypto.run_patch(args.input, args.output, int(args.key1, 16), int(args.key2, 16))
    elif args.command == "structure":
        structurer.run_structure(args.input, args.output, args.format)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
