#!/usr/bin/env python3
"""
Convert an Intel HEX file (covering full flash) into a contiguous padded
binary. Gaps are filled with 0xFF. Intended for generating a combined
bootloader+app padded .bin from ArduPilot's with_bl .hex artifact.

Usage:
  python3 Tools/hex_to_padded_bin.py \
    --hex build/HDZERO_HALO/bin/ardurover_with_bl.hex \
    --out build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin

Notes:
  - Supports Extended Linear Address (type 04) records.
  - Fills any address gaps with 0xFF.
"""

import argparse
import sys


def parse_ihex_record(line):
    if not line.startswith(":"):
        raise ValueError("Invalid IHEX line (no colon)")
    line = line.strip()[1:]
    if len(line) < 10:
        raise ValueError("Invalid IHEX line (too short)")
    try:
        length = int(line[0:2], 16)
        addr = int(line[2:6], 16)
        rectype = int(line[6:8], 16)
        data = bytes.fromhex(line[8:8+length*2])
        checksum = int(line[8+length*2:8+length*2+2], 16)
    except Exception as e:
        raise ValueError(f"Invalid IHEX parsing error: {e}")

    # Verify checksum if needed (optional for our purposes)
    # sum of length, addr high, addr low, rectype, data bytes, checksum == 0 mod 256
    s = length + (addr >> 8) + (addr & 0xFF) + rectype + sum(data)
    s = (s + checksum) & 0xFF
    if s != 0:
        raise ValueError("IHEX checksum mismatch")

    return length, addr, rectype, data


def ihex_to_image(ihex_path):
    image = {}
    min_addr = None
    max_addr = None
    upper = 0  # upper 16 bits for linear address (type 04)

    with open(ihex_path, 'r') as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            length, addr, rectype, data = parse_ihex_record(raw)
            if rectype == 0x00:  # data
                base = (upper << 16) | addr
                for i, b in enumerate(data):
                    a = base + i
                    image[a] = b
                if min_addr is None or base < min_addr:
                    min_addr = base
                end_addr = base + len(data) - 1
                if max_addr is None or end_addr > max_addr:
                    max_addr = end_addr
            elif rectype == 0x01:  # EOF
                break
            elif rectype == 0x04:  # Extended Linear Address
                if length != 2:
                    raise ValueError("Invalid type 04 record length")
                upper = (data[0] << 8) | data[1]
            else:
                # Ignore other record types for this use-case
                continue

    if min_addr is None or max_addr is None:
        raise ValueError("No data records found in HEX")

    return image, min_addr, max_addr


def write_padded_bin(out_path, image, start, end):
    size = end - start + 1
    buf = bytearray([0xFF] * size)
    for a, b in image.items():
        if start <= a <= end:
            buf[a - start] = b
    with open(out_path, 'wb') as f:
        f.write(buf)


def main():
    ap = argparse.ArgumentParser(description='Convert IHEX (with_bl) to padded raw binary')
    ap.add_argument('--hex', required=True, help='Input Intel HEX file (with_bl .hex)')
    ap.add_argument('--out', required=True, help='Output padded .bin path')
    ap.add_argument('--base', default='0x08000000', help='Base start address for output (default 0x08000000)')
    args = ap.parse_args()

    image, min_addr, max_addr = ihex_to_image(args.hex)

    try:
        base = int(args.base, 0)
    except Exception:
        print(f"Invalid base address: {args.base}", file=sys.stderr)
        sys.exit(2)

    # Ensure we start at provided base (typically 0x08000000)
    start = min(base, min_addr)
    end = max_addr

    write_padded_bin(args.out, image, start, end)
    print(f"Wrote {args.out}: {end - start + 1} bytes (addr {hex(start)}..{hex(end)})")


if __name__ == '__main__':
    main()
