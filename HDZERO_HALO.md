# HDZero Halo ArduPilot Port

Complete ArduPilot Rover port for the HDZero Halo flight controller (STM32H743).

## Hardware Summary

- **MCU:** STM32H743 @ 480 MHz
- **IMU:** Single ICM42688P on SPI1 (dual CS probe: PB3/PB4)
- **Flash:** 16MB W25Q128 JEDEC NOR on SPI2 (LittleFS filesystem)
- **RC:** Built-in ELRS on UART1 (PB6/PB7) with embedded defaults
- **Motors:** 4× PWM outputs on TIM3 (PC6-PC9) with bidirectional DShot
- **USB:** OTG1 (PA11/PA12) with forced enable, dual CDC
- **Scripting:** Lua enabled with 100KB heap
- **Sensors:** No barometer, compass probing enabled on I2C1

## Features Optimized For

✅ Combat robots & racing rovers  
✅ ExpressLRS (ELRS) "just works" out of box  
✅ Serial/ESC passthrough via MAVLink  
✅ Heavy Lua scripting (torque counter-steer, drive mixing)  
✅ LittleFS logging to external SPI NOR  
✅ DFU firmware updates (Windows or Linux)  

## Quick Start

### 1. Build Firmware

```bash
./waf configure --board HDZERO_HALO
./waf rover
```

**Output:** `build/HDZERO_HALO/bin/ardurover.bin`

### 2. Generate Bootloader + App Image

```bash
python3 Tools/make_with_bl.py \
  -b Tools/bootloaders/HDZERO_HALO_bl.bin \
  -a build/HDZERO_HALO/bin/ardurover.bin \
  -o build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin
```

**Output:** `ardurover_with_bl_padded.bin` (~1.6 MB, ready for DFU)

### 3. Flash Firmware

#### Windows: STM32CubeProgrammer
1. Put board in DFU mode (hold BOOT, press RESET, release BOOT)
2. Open STM32CubeProgrammer → USB connection
3. Flash `ardurover_with_bl_padded.bin` at address `0x08000000`
4. Disconnect → power cycle

#### Linux: dfu-util (in devcontainer)
```bash
# Auto-detects DFU device and flashes
./Tools/flash_hdzero_halo_dfu.sh
```

Or manually:
```bash
dfu-util -a 0 -s 0x08000000:leave \
  -D build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin
```

### 4. Connect & Configure

- **Mission Planner:** USB CDC port (COM port auto-detects)
- **ELRS:** Pre-configured on UART1 (420kbaud, CRSF, RSSI on channel 15, LQ on 16)
- **Flight modes:** Default channel 12 (matches ELRS hybrid switch)

**No further configuration needed** — ELRS, RSSI, and flight modes work immediately.

## Embedded Defaults

The following parameters are baked into the firmware (`defaults.parm`):

```
SERIAL1_PROTOCOL 23          # RCIN (CRSF)
SERIAL1_BAUD 115             # Start 115200, auto-negotiate to 420k
RSSI_TYPE 3                  # ReceiverProtocol
RC_OPTIONS 8704              # Bit 9: suppress CRSF warnings, Bit 13: ELRS 420k
FLTMODE_CH 12                # Match ELRS hybrid switch default
```

## Serial Port Mapping

| Port | UART | Pins | Default Protocol | Notes |
|------|------|------|------------------|-------|
| SERIAL0 | OTG1 | PA11/PA12 | MAVLink2 | USB (forced enabled) |
| SERIAL1 | USART1 | PB6/PB7 | RCIN (23) | **ELRS** with embedded defaults |
| SERIAL2 | USART2 | PA2/PA3 | MAVLink (1) | Telemetry |
| SERIAL3 | USART3 | PB11 (RX only) | Disabled (-1) | GPS optional |
| SERIAL4 | UART4 | PA1 (RX only) | ESC Telem (16) | ESC telemetry |
| SERIAL5 | UART5 | PC12/PD2 | Disabled (-1) | DisplayPort/VTX optional |
| SERIAL6 | UART7 | PE8/PE7 | Disabled (-1) | User port |
| SERIAL7 | UART8 | PE1/PE0 | Disabled (-1) | User port |

## Serial Passthrough

Use MAVLink `SERIAL_CONTROL` messages for firmware updates and config:

- **ELRS firmware update:** `SERIAL_CONTROL_SERIAL1` (UART1)
- **ESC config/firmware:** `SERIAL_CONTROL_SERIAL4` (UART4) or motor outputs
- **Flags:** `EXCLUSIVE | BLOCKING`

See [ardupilot_passthrough.md](ardupilot_passthrough.md) for detailed workflow.

## Motor Outputs

| Output | Pin | Timer | Modes | Notes |
|--------|-----|-------|-------|-------|
| PWM1 | PC6 | TIM3_CH1 | PWM/DShot/BIDIR | Motor 1 |
| PWM2 | PC7 | TIM3_CH2 | PWM/DShot | Motor 2 |
| PWM3 | PC8 | TIM3_CH3 | PWM/DShot/BIDIR | Motor 3 |
| PWM4 | PC9 | TIM3_CH4 | PWM/DShot | Motor 4 |

**Bidirectional DShot** enabled on outputs 1 & 3 for ESC telemetry.

## Lua Scripting

**Heap:** 100KB (configurable in `hwdef.dat`: `SCRIPTING_HEAP_SIZE`)

**Example scripts:** See `libraries/AP_HAL_ChibiOS/hwdef/HDZERO_HALO/LUA_EXAMPLES.md`
- Torque counter-steer for combat robots
- Drive mode mixing (tank, car, hybrid)
- Memory/CPU profiling via STATUSTEXT

**RAM guidance:** Keep >250KB free after boot. Check via `@SYS/param_table.lua` or custom profiler.

## Filesystem

**LittleFS on 16MB SPI NOR flash** (W25Q128, SPI2 @ 104 MHz)
- **Mount:** `@FLASH/`
- **Logs:** ArduPilot tlog format (no block logging)
- **Lua scripts:** Upload via MAVLink FTP or DFU remount

## Development Environment

### Devcontainer (Recommended)

Includes:
- ARM GCC toolchain
- Python 3.12 + ArduPilot deps
- `dfu-util` for flashing
- USB device passthrough (`/dev/bus/usb`)
- ccache (10GB persistent volume)

**Setup:**
```bash
# Open in VS Code with Remote-Containers extension
code .
# Ctrl+Shift+P → "Reopen in Container"
```

### Manual Setup

```bash
# Install dfu-util
sudo apt install dfu-util

# Configure USB passthrough (if using Docker)
docker run --device=/dev/bus/usb:/dev/bus/usb --privileged ...
```

## Tooling

### `Tools/make_with_bl.py`
Generates padded bootloader+app image with correct offsets.

**Why needed:** STM32 bootloader at `0x08000000`, app at `0x08060000` (384KB offset). Simple concatenation fails; this tool pads correctly.

**Usage:**
```bash
python3 Tools/make_with_bl.py -b <bootloader.bin> -a <app.bin> -o <output.bin>
```

### `Tools/flash_hdzero_halo_dfu.sh`
One-command DFU flash script. Auto-builds padded image if missing.

**Usage:**
```bash
./Tools/flash_hdzero_halo_dfu.sh
```

### `Tools/reboot_to_dfu_bf.py`
Software reboot to DFU for boards running Betaflight (sends `bl` command over CLI).

**Usage:**
```bash
python3 Tools/reboot_to_dfu_bf.py
```

## Pin Reference

### SPI
- **SPI1:** IMU (PA5/PA6/PA7, CS: PB3/PB4)
- **SPI2:** Flash (PB13/PB14/PB15, CS: PB12)

### I2C
- **I2C1:** External compass (PB8/PB9)

### ADC
- **VBAT:** PC0 (scale 11.0)
- **CURR:** PC2 (scale 50.0)
- **RSSI:** PC1 (analog RSSI input)

### Misc
- **LED strip:** PA10 (NeoPixel/WS2812, TIM1_CH3)
- **Beeper:** PD12 (TIM4_CH1, inverted)
- **GPIO:** PE2 (user output)

## Known Issues & Workarounds

### Issue: "Baro: unable to initialise driver"
**Cause:** Board has no barometer; compile-time disabled.  
**Fix:** Already handled in hwdef (`AP_BARO_ENABLED 0`). If you see this, reflash latest firmware.

### Issue: Windows dual CDC "Code 10" on second port
**Cause:** Windows expects both CDC ports functional; second port unused.  
**Fix:** Ignore safely, or disable in Device Manager. Primary MAVLink port (COM lower number) works fine.

### Issue: DFU not detected in WSL2
**Cause:** WSL2 kernel lacks USBIP support for `usbipd attach`.  
**Fix:** Flash from Windows (STM32CubeProgrammer) or use devcontainer with native Docker USB passthrough.

## Future Enhancements

- [ ] Add DRDY/EXTI pins for IMU (PC13, PA15) to improve sensor timing
- [ ] CAN bus support (PD0/PD1 available, not configured)
- [ ] OSD via MAX7456 on SPI3 (if hardware supports)
- [ ] Bench Lua profiling script for memory/CPU monitoring

## Hardware Variants

**Note:** Some Halo boards ship with MPU6000 instead of ICM42688P. The hwdef probes both CS pins (PB3/PB4) to auto-detect the installed chip.

## References

- **Betaflight config:** `betaflight/config/configs/HDZERO_HALO/config.h`
- **ArduPilot docs:** [ardupilot.org/rover](https://ardupilot.org/rover/)
- **ELRS setup:** [ExpressLRS ArduPilot guide](https://www.expresslrs.org/quick-start/receivers/ardupilot-setup/)
- **Serial passthrough:** `ardupilot_passthrough.md` (in this repo)

## License

ArduPilot is licensed under GPLv3. This port maintains that license.

## Changelog

### v1.0 (November 2025)
- Initial HDZERO_HALO Rover port
- Single ICM42688P IMU support with dual CS probe
- ELRS embedded defaults for plug-and-play RC
- LittleFS on 16MB SPI NOR flash
- Lua scripting (100KB heap)
- DFU tooling and devcontainer
- No barometer, compass optional
- Bidirectional DShot on motor outputs 1 & 3

## Author

Ported by [@your-github-handle] for combat robotics and racing rover applications.

## Support

For issues, open a GitHub issue on your fork or the main ArduPilot repository (if upstreaming).
