#!/usr/bin/env bash
set -euo pipefail

# Simple helper to flash HDZERO_HALO Rover firmware via dfu-util
# Usage:
#   Tools/flash_hdzero_halo_dfu.sh [path/to/firmware.bin]
# Defaults to build/HDZERO_HALO/bin/ardurover_with_bl.bin

DEFAULT_BIN="build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin"
BIN_PATH="${1:-$DEFAULT_BIN}"

if [[ ! -f "$BIN_PATH" ]]; then
  echo "No padded combined image found at '$BIN_PATH'"
  echo "Attempting to generate it..."
  # Preferred: convert the generated with_bl HEX into a padded BIN
  HEX_IN="build/HDZERO_HALO/bin/ardurover_with_bl.hex"
  if [[ -f "$HEX_IN" ]]; then
    echo "Found $HEX_IN, converting to padded BIN..."
    python3 Tools/hex_to_padded_bin.py --hex "$HEX_IN" --out "$BIN_PATH"
  else
    echo "with_bl HEX not found; falling back to bootloader+app padding"
    BL="Tools/bootloaders/HDZERO_HALO_bl.bin"
    APP="build/HDZERO_HALO/bin/ardurover.bin"
    if [[ ! -f "$BL" || ! -f "$APP" ]]; then
      echo "Missing inputs: $HEX_IN or ($BL and/or $APP) not found."
      echo "Please build the app and ensure inputs exist, or pass a custom .bin path."
      exit 1
    fi
    python3 Tools/make_with_bl.py -b "$BL" -a "$APP" -o "$BIN_PATH"
  fi
fi

# Require dfu-util in PATH
if ! command -v dfu-util >/dev/null 2>&1; then
  echo "dfu-util not found. Inside the devcontainer it should be preinstalled."
  echo "If not, run: sudo apt-get update && sudo apt-get install -y dfu-util"
  exit 2
fi

cat <<EOF
=== DFU Flash Helper ===
- Binary: $BIN_PATH
- Tip: Put board in DFU mode (BOOT0 + reset, or vendor-specific combo).
- We'll try to flash to 0x08000000 and leave DFU on success.
EOF

# List DFU devices for user confirmation
if ! dfu-util -l; then
  echo "No DFU device found. Ensure the board is in DFU mode and USB is passed to the container."
  exit 3
fi

echo
read -r -p "Proceed to flash '$BIN_PATH'? [y/N] " ans
case "${ans:-n}" in
  y|Y) ;;
  *) echo "Aborted."; exit 0;;
 esac

# Use sudo to ensure access to /dev/bus/usb when needed
# Altsetting 0 is commonly Internal Flash on STM32 (0483:df11)
set -x
sudo dfu-util -a 0 -s 0x08000000:leave -D "$BIN_PATH"
set +x

echo "Flash complete. If it doesn't reboot automatically, power-cycle the board."
