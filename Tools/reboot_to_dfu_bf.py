#!/usr/bin/env python3
import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except Exception as e:
    print("pyserial missing; install with: pip3 install pyserial", file=sys.stderr)
    sys.exit(2)


def find_default_port():
    # Prefer ACM/USB serials
    ports = list(list_ports.comports())
    preferred = [p.device for p in ports if any(x in p.device for x in ("ACM", "USB", "tty.usb"))]
    return preferred[0] if preferred else (ports[0].device if ports else None)


def main():
    ap = argparse.ArgumentParser(description="Reboot Betaflight into DFU (ROM bootloader) by sending 'bl' over CLI")
    ap.add_argument("--port", "-p", default=find_default_port(), help="Serial device (default: auto-detected)")
    ap.add_argument("--baud", "-b", type=int, default=115200, help="Baudrate (default: 115200)")
    args = ap.parse_args()

    if not args.port:
        print("No serial ports found. Plug the FC in normal mode (not DFU).", file=sys.stderr)
        sys.exit(1)

    print(f"Opening {args.port} @ {args.baud} ...")
    try:
        with serial.Serial(args.port, args.baud, timeout=1) as ser:
            # wake CLI
            ser.write(b"\r\n")
            ser.flush()
            time.sleep(0.2)
            # send Betaflight bootloader command
            ser.write(b"bl\r\n")
            ser.flush()
            print("Sent 'bl'. Device should disconnect and re-enumerate as DFU (0483:df11).")
            print("Run: dfu-util -l  (then flash with Tools/flash_hdzero_halo_dfu.sh)")
    except serial.SerialException as e:
        print(f"Serial error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
