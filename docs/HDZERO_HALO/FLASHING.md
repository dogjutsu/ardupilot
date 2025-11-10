# HDZERO_HALO DFU Flashing (Devcontainer)

Prereqs: the devcontainer maps USB and includes `dfu-util`.
Put the board in DFU mode (STM32 ROM bootloader, usually `0483:df11`).
Verify the device is visible inside the container: `lsusb` or `dfu-util -l`.

## One-liner

```bash
Tools/flash_hdzero_halo_dfu.sh
```

Default binary: `build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin` (bootloader + padding + app).
To specify a file:

```bash
Tools/flash_hdzero_halo_dfu.sh /ardupilot/build/HDZERO_HALO/bin/ardurover_with_bl.bin
```

## Why padding matters
Bootloader reserves the first 384KB of flash (0x08000000..0x0805FFFF). The application must begin exactly at 0x08060000. A simple concatenation places the app too early and leaves the device stuck in the bootloader. The helper script pads with 0xFF so the app aligns correctly.

## Notes
- If you see permissions errors, the script uses `sudo` which should work inside the container.
- If no DFU device is listed, ensure USB is passed through and the board is in DFU mode.
- After initial DFU flash, prefer `.apj` updates via Mission Planner/QGC.

## Entering DFU
- Hardware: hold BOOT while plugging USB, or short BOOT0 to 3V3 and tap RESET.
- Betaflight (software): if the board currently runs Betaflight, you can reboot to DFU via CLI.

```bash
python3 Tools/reboot_to_dfu_bf.py
# or specify a port
python3 Tools/reboot_to_dfu_bf.py -p /dev/ttyACM0
```

You should then see the DFU device in `dfu-util -l` as `0483:df11`.