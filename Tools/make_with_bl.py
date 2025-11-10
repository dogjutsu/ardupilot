#!/usr/bin/env python3
import argparse
import os
import sys

APP_OFFSET_KB = 384  # must match FLASH_BOOTLOADER_LOAD_KB
APP_OFFSET = APP_OFFSET_KB * 1024


def readbin(path):
    with open(path, 'rb') as f:
        return f.read()


def writebin(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def main():
    ap = argparse.ArgumentParser(description='Create padded bootloader+app binary at 0x08000000 with app at 0x08060000')
    ap.add_argument('--bootloader', '-b', required=True, help='Bootloader .bin (placed at 0x08000000)')
    ap.add_argument('--app', '-a', required=True, help='Application .bin (placed at 0x08060000)')
    ap.add_argument('--out', '-o', default='build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin', help='Output combined binary')
    args = ap.parse_args()

    bl = readbin(args.bootloader)
    app = readbin(args.app)

    if len(bl) > APP_OFFSET:
        print(f"Error: bootloader ({len(bl)} bytes) larger than reserved {APP_OFFSET} bytes", file=sys.stderr)
        sys.exit(2)

    pad_len = APP_OFFSET - len(bl)
    combined = bl + (b'\xFF' * pad_len) + app
    writebin(args.out, combined)
    print(f"Wrote {args.out}: {len(combined)} bytes (BL {len(bl)}, pad {pad_len}, APP {len(app)})")


if __name__ == '__main__':
    main()
