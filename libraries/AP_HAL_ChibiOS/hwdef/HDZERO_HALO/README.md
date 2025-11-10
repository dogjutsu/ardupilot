
# HDZero Halo Flight Controller (ArduPilot hwdef)

The HDZero Halo is a compact H7-based flight controller. This README documents
the changes made to produce an ArduPilot `hwdef.dat` starting from the
`TMotorH743/hwdef.dat` baseline. Betaflight's per-board config for HDZERO_HALO
(`betaflight/config/configs/HDZERO_HALO/config.h`) was used as the primary
reference for pin mappings, IMU and external flash choices.

Summary of differences (with justification)

- MCU and clock: kept as STM32H743 at 480 MHz (both boards use this MCU).
  - Reason: Betaflight reports `FC_TARGET_MCU STM32H743` for the Halo.

- Oscillator / HSE: set to 8 MHz.  
  - Reason: Betaflight uses 8 MHz; the Halo schematic (if available) should be
    checked, but 8 MHz is the common default for many H7 flight controllers.

- SPI / IMU layout: SPI1 = PA5/PA6/PA7, SPI2 = PB13/PB14/PB15.  
  - Reason: Matches Betaflight mapping. IMU chip-select pins are PB3 (ICM42688). For our internal build we use a single ICM42688.
  - IMUs declared: ICM42688 only (single IMU).

- External flash (W25Q128) on PB12 using SPI2.  
  - Reason: Betaflight sets `USE_FLASH_W25Q128FV` and `FLASH_CS_PIN PB12` and
    `FLASH_SPI_INSTANCE SPI2`.

- UART mapping: follow Betaflight pins: USART1(PB6/PB7), USART2(PA2/PA3),
  USART3(PB11), UART4(PA1), UART5(PC12/PD2), UART7(PE8/PE7), UART8(PE1/PE0).
  - Reason: Ensures serial peripherals in ArduPilot align with physical pins used
    by Betaflight for the Halo. Defaults set for Rover use: SERIAL1=RCIN (ELRS), SERIAL2=MAVLink, SERIAL4=ESC Telemetry. SERIAL3/SERIAL5 disabled.

- PWM outputs: map MOTOR1..4 to PC6..PC9 using TIM3 CH1..CH4; repurpose beeper PD12 (TIM4_CH1) as PWM5.  
  - Reason: Betaflight uses PC6..PC9 for motors; using TIM3 matches many H7 hwdefs. PD12 provides an additional PWM-capable output for weapon ESCs on combat robots.

- Bootloader flashing disabled by default (`AP_BOOTLOADER_FLASHING_ENABLED 0`).  
  - Reason: This repo does not include an HDZERO_HALO bootloader binary, and
    the chibios hwdef scripts will error if `AP_BOOTLOADER_FLASHING_ENABLED` is
    enabled without a bootloader file. Use `Tools/scripts/build_bootloaders.py`
    to produce a bootloader if you want to enable flashing.

PWM/Outputs Mapping

| Output | Pin | Timer/Channel | Notes |
|-------:|-----|----------------|-------|
| PWM1 | PC6 | TIM3_CH1 | Motor/ESC |
| PWM2 | PC7 | TIM3_CH2 | Motor/ESC |
| PWM3 | PC8 | TIM3_CH3 | Motor/ESC |
| PWM4 | PC9 | TIM3_CH4 | Motor/ESC |
| PWM5 | PD12 | TIM4_CH1 | Repurposed from beeper; use for weapon ESC |

Notes:
- All outputs support PWM and DShot; BiDir DShot available via SERVO_BLH_BDMASK.
- Beeper is removed by default; add a beeper only if you remap it to another pin.

How to test

1. Re-open the devcontainer (or run the `ardupilot-dev:local` image) and from
   the repo root run:

```bash
. ./.venv/bin/activate
./waf configure --board HDZERO_HALO
```

2. If the configure step emits more hwdef parser errors, fix them iteratively in
   `hwdef.dat` (the parser prints helpful messages indicating missing values).

3. After configure succeeds, try a minimal build target to ensure compilation
   and linkage succeed.

Files updated

- `hwdef.dat` — the new HDZERO_HALO hardware definition derived from TMotorH743.
- `README.md` — this file with the rationale and testing steps.
  - Updated to include PWM5 on PD12 (beeper repurposed).

References

- `betaflight/config/configs/HDZERO_HALO/config.h` — used as the primary
  cross-reference for pin and peripheral mapping.
- `libraries/AP_HAL_ChibiOS/hwdef/TMotorH743/hwdef.dat` — source baseline.

Additional notes (internal build)

- Lua scripting: enabled by default with a 100KB heap (`SCRIPTING_HEAP_SIZE 100000`). Increase only if RAM headroom allows; aim for >250KB free RAM after build.
- Heap sizing guidance: start at 100KB. If free RAM after boot dips below ~250KB, reduce to 80KB. If scripts require more complex buffers and free RAM >400KB, you may raise to 120KB. Profile by adding a lightweight Lua script that reports `collectgarbage('count')` and approximate free memory via MAVLink STATUSTEXT.
- Passthrough over USB (MAVLink SERIAL_CONTROL):
  - ELRS firmware updates via UART1 (device `SERIAL_CONTROL_SERIAL1`).
  - ESC firmware/config tools via UART2/4/7/8 as needed (devices `SERIAL_CONTROL_SERIAL2`, etc.).
  - Use EXCLUSIVE | BLOCKING flags; ArduPilot disables flow control during bootloader comms.
- GPS/DisplayPort: disabled by default for combat robots.
- CAN: not configured; PD0/PD1 are typical CAN1 pins on H743 and can be mapped later if needed.
- PWM outputs: PC6..PC9 via TIM3 CH1..4; suitable for PWM/DSHOT.
 - Hybrid control recommendation: use Lua at 20–50Hz for supervisory logic (bias calculation, mode gating). For sub-10ms torque counter-steer, implement a small C++ module publishing a filtered `torque_bias_yaw` value to a parameter Lua reads. This keeps high-rate fusion out of the scripting VM.
 - Passthrough device IDs: ArduPilot maps `SERIAL_CONTROL_SERIAL0+N` to `SERIALN`. Example: ELRS on SERIAL1 => device=SERIAL_CONTROL_SERIAL1.


