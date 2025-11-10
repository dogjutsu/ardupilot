# HDZero Halo Configuration & Usage Guide

Complete reference for configuring and using ArduPilot Rover on the HDZero Halo flight controller. This guide covers hardware setup, firmware configuration, Lua scripting, and combat robotics-specific tuning.

---

## Table of Contents

1. [Hardware Overview](#hardware-overview)
2. [Firmware Installation](#firmware-installation)
3. [Initial Configuration](#initial-configuration)
4. [Serial Port Configuration](#serial-port-configuration)
5. [Motor & ESC Setup](#motor--esc-setup)
6. [RC Input (ExpressLRS)](#rc-input-expresslrs)
7. [Lua Scripting](#lua-scripting)
8. [Data Logging](#data-logging)
9. [Combat Robot Tuning](#combat-robot-tuning)
10. [Advanced Features](#advanced-features)
11. [Troubleshooting](#troubleshooting)
12. [Parameter Reference](#parameter-reference)

---

## Hardware Overview

### Board Specifications

- **MCU:** STM32H743 @ 480 MHz
- **Flash:** 2MB internal + 16MB W25Q128 SPI NOR (LittleFS)
- **RAM:** 1MB (SRAM + DTCM + AXI SRAM)
- **IMU:** ICM42688P on SPI1 (hardware variants may have MPU6000)
- **Barometer:** None (disabled in firmware)
- **Compass:** Optional external I2C (auto-detected)
- **USB:** OTG1 (PA11/PA12), dual CDC ports
- **RC:** Built-in ELRS receiver on UART1

### Pin Mappings

#### SPI Buses
- **SPI1 (IMU):** PA5/PA6/PA7, CS: PB3 (GYRO2), PB4 (GYRO1)
- **SPI2 (Flash):** PB13/PB14/PB15, CS: PB12

#### Serial Ports
| Port | UART | TX | RX | Default Protocol |
|------|------|----|----|------------------|
| SERIAL0 | OTG1 | USB | USB | MAVLink2 |
| SERIAL1 | USART1 | PB6 | PB7 | RCIN (ELRS) |
| SERIAL2 | USART2 | PA2 | PA3 | MAVLink |
| SERIAL3 | USART3 | - | PB11 | Disabled |
| SERIAL4 | UART4 | - | PA1 | ESC Telemetry |
| SERIAL5 | UART5 | PC12 | PD2 | Disabled |
| SERIAL6 | UART7 | PE8 | PE7 | Disabled |
| SERIAL7 | UART8 | PE1 | PE0 | Disabled |

#### Motor Outputs (PWM/DShot)
| Output | Pin | Timer | BIDIR Support |
|--------|-----|-------|---------------|
| PWM1 | PC6 | TIM3_CH1 | ✅ Yes |
| PWM2 | PC7 | TIM3_CH2 | ❌ No |
| PWM3 | PC8 | TIM3_CH3 | ✅ Yes |
| PWM4 | PC9 | TIM3_CH4 | ❌ No |

#### I2C / Sensors
- **I2C1:** PB8 (SCL), PB9 (SDA) - External compass
- **VBAT:** PC0 (11:1 divider)
- **CURR:** PC2 (50A/V scale)
- **RSSI:** PC1 (analog)

#### Misc
- **LED Strip:** PA10 (NeoPixel/WS2812)
- **Beeper:** PD12 (inverted)
- **GPIO:** PE2 (user output)

---

## Firmware Installation

### Prerequisites

- STM32CubeProgrammer (Windows) or `dfu-util` (Linux/devcontainer)
- USB cable
- Firmware binary: `ardurover_with_bl_padded.bin`

### Building from Source

```bash
# In devcontainer or Linux environment
./waf configure --board HDZERO_HALO
./waf rover

# Generate bootloader + app combined image
python3 Tools/make_with_bl.py \
  -b Tools/bootloaders/HDZERO_HALO_bl.bin \
  -a build/HDZERO_HALO/bin/ardurover.bin \
  -o build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin
```

### Flashing via DFU

#### Windows (STM32CubeProgrammer)
1. **Enter DFU mode:** Hold BOOT button, press RESET, release BOOT
2. Open STM32CubeProgrammer
3. Select "USB" connection, click "Connect"
4. Download tab → File path: `ardurover_with_bl_padded.bin`
5. Start address: `0x08000000`
6. Click "Start Programming"
7. Disconnect and power cycle

#### Linux (dfu-util)
```bash
# Automated script
./Tools/flash_hdzero_halo_dfu.sh

# Or manual
dfu-util -a 0 -s 0x08000000:leave \
  -D build/HDZERO_HALO/bin/ardurover_with_bl_padded.bin
```

### Updating Firmware via Mission Planner

After initial DFU flash, future updates can be done via USB using Mission Planner:
1. Connect board via USB
2. Mission Planner → Setup → Install Firmware → Load Custom Firmware
3. Select `ardurover.apj` from `build/HDZERO_HALO/bin/`

---

## Initial Configuration

### Default Parameters (Pre-configured)

The firmware includes embedded defaults for plug-and-play ELRS operation:

```
SERIAL1_PROTOCOL = 23        # RCIN (CRSF)
SERIAL1_BAUD = 115           # 115200 → auto-negotiates to 420k
RSSI_TYPE = 3                # ReceiverProtocol
RC_OPTIONS = 8704            # Bits 9,13: CRSF warnings suppressed, ELRS 420k
FLTMODE_CH = 12              # Flight mode channel (ELRS switch)
```

### First Boot Checklist

1. **Connect via Mission Planner** (USB)
2. **Verify sensors:**
   - IMU shows green (INS)
   - No barometer errors (baro disabled)
   - GPS: not required (shows "No GPS" - normal)
3. **Calibrate accelerometer:** Setup → Mandatory Hardware → Accel Calibration
4. **Calibrate compass** (if external): Setup → Mandatory Hardware → Compass

### Frame Type Selection

For combat robots/rovers:
```
FRAME_CLASS = 1              # Rover
FRAME_TYPE = 1               # Skid-steer (tank drive)
                             # or 0 for car/Ackermann
```

---

## Serial Port Configuration

### ExpressLRS (UART1) - Pre-configured

No additional configuration needed! ELRS works out of box with:
- **Protocol:** CRSF (protocol 23)
- **Baud:** Auto-negotiates from 115200 → 420000
- **RSSI:** Channel 15 (ReceiverProtocol)
- **Link Quality:** Channel 16 (ReceiverProtocol)

#### ELRS Channel Mapping
```
CH1  = Roll/Steer
CH2  = Pitch
CH3  = Throttle
CH4  = Yaw
CH5+ = Aux channels (switches)
CH12 = Flight mode switch (default)
CH15 = RSSI (automatic)
CH16 = Link Quality (automatic)
```

### Telemetry Radio (UART2)

For 915MHz/433MHz telemetry:
```
SERIAL2_PROTOCOL = 1         # MAVLink1 (or 2 for MAVLink2)
SERIAL2_BAUD = 57            # 57600 (common for telemetry radios)
```

### GPS (UART3) - Optional

```
SERIAL3_PROTOCOL = 5         # GPS
SERIAL3_BAUD = 115           # 115200 (u-blox default)
GPS_TYPE = 1                 # Auto (or specific GPS type)
```

### ESC Telemetry (UART4) - Pre-configured

Receives telemetry from ESC:
```
SERIAL4_PROTOCOL = 16        # ESC Telemetry
SERIAL4_BAUD = 115           # 115200 (common for BLHeli telemetry)
```

### Custom Serial Usage (UART5/7/8)

Available for:
- Secondary GPS
- Lidar/rangefinder
- Companion computer (Raspberry Pi, etc.)
- Custom Lua serial drivers

Example (Lidar on UART7):
```
SERIAL6_PROTOCOL = 9         # Rangefinder
SERIAL6_BAUD = 115
RNGFND1_TYPE = 8             # LightWareSerial (or appropriate type)
```

---

## Motor & ESC Setup

### DShot Configuration

**Recommended for combat robots:**

```
# Enable DShot600
SERVO1_FUNCTION = 73         # ThrottleLeft (or specific motor assignment)
SERVO2_FUNCTION = 74         # ThrottleRight
MOT_PWM_TYPE = 4             # DShot600 (or 5 for DShot1200)

# Bidirectional DShot (ESC telemetry via motor signal)
SERVO_BLH_BDMASK = 5         # Binary 0101 = enable on outputs 1 & 3
```

**Available on outputs 1 & 3 only** (TIM3 hardware limitation).

### Standard PWM Configuration

For brushed motors or non-DShot ESCs:

```
MOT_PWM_TYPE = 0             # Normal PWM
SERVO1_MIN = 1000            # Minimum PWM
SERVO1_MAX = 2000            # Maximum PWM
SERVO1_TRIM = 1500           # Neutral
```

### ESC Telemetry

#### Via UART4 (BLHeli passthrough)
Pre-configured for receiving telemetry packets from ESC.

#### Via Bidirectional DShot
Enable on supported outputs (1 & 3):
```
SERVO_BLH_BDMASK = 5         # Outputs 1 & 3
SERVO_BLH_TRATE = 10         # 10Hz telemetry rate
```

Telemetry provides:
- RPM
- Voltage
- Current
- Temperature
- Consumption (mAh)

---

## RC Input (ExpressLRS)

### Pre-configured Settings

The firmware includes optimal ELRS defaults. **No configuration needed!**

### Flight Mode Configuration

Default: Channel 12 (3-position switch)

```
FLTMODE_CH = 12
FLTMODE1 = 0                 # Manual
FLTMODE2 = 1                 # Acro
FLTMODE3 = 4                 # Hold
```

**Common modes for combat robots:**
- **0 (Manual):** Direct RC control
- **1 (Acro):** Rate control with stabilization
- **4 (Hold):** Position hold (requires GPS)
- **10 (Auto):** Autonomous missions

### RC Failsafe

```
FS_THR_ENABLE = 1            # Enable throttle failsafe
FS_THR_VALUE = 950           # PWM below this = failsafe
FS_ACTION = 2                # Action: Hold position (or 0=nothing, 1=RTL)
FS_TIMEOUT = 3               # Seconds before failsafe
```

### Channel Reversing

If controls are backwards:
```
RC1_REVERSED = 1             # Reverse roll/steer
RC3_REVERSED = 1             # Reverse throttle
```

---

## Lua Scripting

### Heap Configuration

**Default:** 100KB heap (conservative for 1MB RAM)

**Tuning guidance:**
- **80KB:** Minimal scripts, tight RAM budget
- **100KB:** Default, supports most applications
- **120KB+:** Complex multi-script setups (verify >250KB free RAM)

Change in `hwdef.dat`:
```
SCRIPTING_HEAP_SIZE 100000
```

### Script Locations

Upload scripts to `@FLASH/scripts/` via:
1. **MAVLink FTP:** Mission Planner → Data → File Transfer
2. **USB mass storage:** Recompile with mass storage enabled
3. **Mission Planner:** Config → User Params → Upload

### Example Scripts

See `LUA_EXAMPLES.md` for complete examples.

#### 1. Torque Counter-Steer (Combat Robots)

Compensates for weapon reaction torque using IMU yaw rate and ESC telemetry.

```lua
-- Simplified outline
function update()
  local yaw_rate = ahrs:get_gyro():z()  -- rad/s
  local weapon_current = -- read from ESC telemetry
  
  local steer_bias = -0.02 * yaw_rate - 0.001 * weapon_current
  
  -- Mix into steering output
  local rc_steer = rc:get_pwm(1)
  local adjusted_steer = rc_steer + (steer_bias * 500)
  SRV_Channels:set_output_pwm(0, adjusted_steer)
  
  return update, 20  -- 50Hz
end

return update()
```

#### 2. Traction Control

Reduces throttle when high motor current + low acceleration = wheel slip.

```lua
function update()
  local motor_current = -- from ESC telemetry
  local accel_x = ahrs:get_accel():x()
  
  if motor_current > 30 and math.abs(accel_x) < 0.5 then
    -- Reduce throttle 5%
    local throttle = rc:get_pwm(3)
    SRV_Channels:set_output_pwm(1, throttle * 0.95)
  end
  
  return update, 50  -- 20Hz
end

return update()
```

#### 3. Weapon Safety Interlock

Disable weapon output unless armed and specific switch is active.

```lua
function update()
  local armed = arming:is_armed()
  local weapon_enable = rc:get_pwm(6) > 1700  -- CH6 switch
  
  if armed and weapon_enable then
    SRV_Channels:set_output_pwm(2, rc:get_pwm(5))  -- Weapon control on CH5
  else
    SRV_Channels:set_output_pwm(2, 1500)  -- Weapon off
  end
  
  return update, 100  -- 10Hz
end

return update()
```

### Performance Monitoring

Add to any script:
```lua
gcs:send_text(6, string.format("Lua mem: %.1f KB", collectgarbage("count")))
gcs:send_text(6, string.format("Free RAM: %d KB", hal.mem_free() / 1024))
```

### Best Practices

1. **Keep scripts simple:** Offload high-rate math to C++ modules
2. **Target 20-50Hz:** Balance responsiveness vs CPU load
3. **Test in SITL first:** `sim_vehicle.py -v Rover --add-param-file=...`
4. **Profile memory:** Watch heap usage via GCS messages
5. **Error handling:** Wrap risky operations in `pcall()`
6. **Modular design:** Split complex logic into multiple scripts

---

## Data Logging

### LittleFS External Flash

**Storage:** 16MB W25Q128 on SPI2
**Mount point:** `@FLASH/`
**Format:** ArduPilot `.bin` tlog format

### Log Configuration

```
LOG_BACKEND_TYPE = 4         # Block logging disabled, use LittleFS
LOG_FILE_DSRMROT = 1         # Disable log rotation (combat use)
LOG_BITMASK = 131071         # Log everything (or customize)
```

**Common bitmasks:**
- `131071`: Everything (default)
- `65535`: Most data, less CPU load
- Custom: Use Mission Planner → Config → Full Parameter List → LOG_BITMASK calculator

### Log Retrieval

1. **Mission Planner:** Data → DataFlash Logs → Download
2. **MAVLink FTP:** File browser access to `@FLASH/logs/`
3. **USB mass storage:** Requires custom build with mass storage enabled

### Log Analysis

**Mission Planner:**
- Data → DataFlash Logs → Review a Log
- Graph any parameter: time-series plots, FFT, etc.

**MAVExplorer (advanced):**
```bash
MAVExplorer.py logfile.bin
# Interactive Python-based analysis
```

---

## Combat Robot Tuning

### Drive Characterization

#### Skid-Steer (Tank Drive)

```
# Motor mixing
FRAME_CLASS = 1              # Rover
FRAME_TYPE = 1               # Skid-steer

# Steering aggressiveness
ATC_STR_RAT_P = 0.2          # Steering rate P gain (start low)
ATC_STR_RAT_D = 0.01         # Steering rate D gain

# Throttle response
ATC_SPEED_P = 0.2            # Speed P gain
ATC_SPEED_I = 0.3            # Speed I gain (reduce for combat)
ATC_SPEED_D = 0.0            # Usually zero

# Turn rate limiting
ATC_TURN_MAX_G = 0.5         # Max turn rate (g-force, combat needs higher)
```

#### Car/Ackermann Steering

```
FRAME_TYPE = 0               # Ackermann

# Steering servo limits
SERVO1_MIN = 1000
SERVO1_MAX = 2000
SERVO1_TRIM = 1500           # Center position

# Steering rate
ATC_STR_RAT_P = 0.5
ATC_STR_RAT_I = 0.1
```

### Weapon Integration

#### Brushless Weapon Motor

Connect to PWM output (e.g., PWM3):

```
SERVO3_FUNCTION = 0          # Disabled (manual control via Lua)
SERVO3_MIN = 1000
SERVO3_MAX = 2000
```

Control via:
1. **Direct RC passthrough:** Lua script maps RC channel to output
2. **Rate limiting:** Slow spinup/spindown for safety
3. **Torque compensation:** Adjust drive based on weapon current

#### Spinner RPM Monitoring

Via ESC telemetry (bidirectional DShot):
```
SERVO_BLH_BDMASK = 4         # Enable on output 3
```

Access in Lua:
```lua
local rpm = esc_telem:get_rpm(2)  -- 0-indexed, output 3 = index 2
```

### Impact Detection

Use IMU accelerometer to detect hits:

```lua
local impact_threshold = 50.0  -- m/s² (adjust for robot mass)

function update()
  local accel = ahrs:get_accel()
  local accel_mag = math.sqrt(accel:x()^2 + accel:y()^2 + accel:z()^2)
  
  if accel_mag > impact_threshold then
    gcs:send_text(0, "IMPACT DETECTED!")
    -- Optional: trigger camera, reduce throttle, etc.
  end
  
  return update, 100  -- 10Hz
end
```

### Gyro Drift Compensation

Combat robots experience high vibration. Increase gyro filter cutoffs:

```
INS_GYRO_FILTER = 40         # Increase from 20 (default) to 40+
INS_ACCEL_FILTER = 20        # Increase from 10 to 20
```

### Battery Monitoring

```
BATT_MONITOR = 4             # Analog voltage & current
BATT_VOLT_PIN = 10           # PC0 (VBAT)
BATT_CURR_PIN = 11           # PC2 (CURR)
BATT_VOLT_MULT = 11.0        # 11:1 divider
BATT_AMP_PERVLT = 50.0       # 50A/V sensor

# Low battery failsafe
BATT_LOW_VOLT = 3.3          # Per-cell low voltage (3S = 9.9V total)
BATT_CRT_VOLT = 3.0          # Per-cell critical (3S = 9.0V)
BATT_FS_LOW_ACT = 2          # Action: Land/Disarm
```

---

## Advanced Features

### Serial Passthrough (ESC/ELRS Configuration)

Update ESC firmware or ELRS settings without disassembly.

#### ELRS Update via UART1

**Mission Planner:**
1. Setup → Optional Hardware → Passthrough
2. Select: `SERIAL1` (UART1)
3. Connect ELRS Configurator, update as normal

**Python script:**
```python
from pymavlink import mavutil

master = mavutil.mavlink_connection('COM11')
master.mav.serial_control_send(
    mavutil.mavlink.SERIAL_CONTROL_DEV_SERIAL1,  # UART1
    mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | 
    mavutil.mavlink.SERIAL_CONTROL_FLAG_BLOCKING,
    0, 0, bytearray(data)
)
```

#### ESC Configuration via Motor Outputs

Use `SERVO_PASSTHROUGH` or BLHeli suite passthrough.

### Autonomous Missions (Optional)

Requires GPS (UART3).

#### Simple Point-to-Point

1. Mission Planner → Flight Plan
2. Right-click map → Add Waypoint
3. Set waypoint commands:
   - `WAYPOINT`: Navigate to point
   - `DO_SET_SERVO`: Trigger weapon
   - `DELAY`: Wait X seconds
4. Upload → Switch to Auto mode

#### Geofencing

Prevent robot from leaving arena:

```
FENCE_ENABLE = 1             # Enable fence
FENCE_TYPE = 2               # Polygon fence
FENCE_ACTION = 1             # RTL (or 4=brake)
FENCE_RADIUS = 50            # Max distance from home (meters)
```

### Companion Computer Integration

Connect Raspberry Pi/Jetson via UART7:

```
SERIAL6_PROTOCOL = 2         # MAVLink2
SERIAL6_BAUD = 921           # 921600 (high-speed)

# Enable onboard computer control
SYSID_MYGCS = 255            # Accept commands from GCS
RC_OVERRIDE_TIME = 3         # RC override timeout
```

Python example:
```python
from dronekit import connect, VehicleMode

vehicle = connect('/dev/ttyS6', baud=921600)
vehicle.mode = VehicleMode("GUIDED")
vehicle.simple_goto(location)
```

### OSD (Analog Video) - Future

Requires MAX7456 on SPI3 (not currently configured).

To enable (requires hardware mod + hwdef change):
```
OSD_TYPE = 1                 # MAX7456
# Add SPI3 pins and CS to hwdef.dat
```

---

## Troubleshooting

### Board Not Detected (USB)

**Symptoms:** COM port not appearing

**Solutions:**
1. Check USB cable (must be data cable, not charge-only)
2. Install STM32 Virtual COM Port driver (Windows)
3. Try different USB port
4. Verify `HAL_USB_FORCE` in hwdef (already enabled)

### ELRS Not Connecting

**Symptoms:** "No RC receiver" or "RC failsafe"

**Checks:**
1. Verify `SERIAL1_PROTOCOL = 23`
2. Check `RC_OPTIONS = 8704` (bits 9,13 set)
3. ELRS bound to transmitter (LED solid)
4. Correct UART1 wiring (TX→RX, RX→TX, GND)

**Force rebind:**
```
# Mission Planner → Setup → Optional Hardware → Passthrough
# Select SERIAL1, use ELRS Configurator
```

### IMU Not Initializing

**Symptoms:** "INS: unable to initialise driver"

**Causes:**
1. Wrong CS pin (should be PB3 or PB4)
2. SPI wiring issue
3. IMU chip variant (MPU6000 vs ICM42688P)

**Dual probe enabled:** Firmware tries both CS pins automatically.

### High CPU Load / Lua Timeout

**Symptoms:** "Lua: exceeded 100ms runtime", slow response

**Solutions:**
1. Reduce script update frequency (50Hz → 20Hz)
2. Simplify calculations (avoid expensive operations)
3. Profile: add timing prints
   ```lua
   local start = micros()
   -- your code
   local elapsed = micros() - start
   gcs:send_text(6, string.format("Exec: %d us", elapsed))
   ```
4. Reduce heap size if memory fragmentation is issue

### Flash Logging Not Working

**Symptoms:** "No logs", `@FLASH/logs/` empty

**Checks:**
1. Verify W25Q128 detected at boot (check messages)
2. Format flash: `FLASH_FORMAT = 1` (one-time)
3. Check `LOG_BACKEND_TYPE` and `LOG_BITMASK`
4. Free space: logs auto-delete oldest when full

### Calibration Issues

**Accelerometer won't calibrate:**
- Ensure flat, stable surface
- Use mission planner "Level" button first
- Disable vibration-sensitive scripts during calibration

**Compass interference:**
- Move away from motors/ESCs/magnets
- Use external compass on mast
- Set `COMPASS_USE = 0` if not using GPS

---

## Parameter Reference

### Critical Parameters (Combat Robots)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `FRAME_CLASS` | 1 | Rover |
| `FRAME_TYPE` | 1 | Skid-steer (tank) |
| `SERIAL1_PROTOCOL` | 23 | RCIN (ELRS) |
| `RC_OPTIONS` | 8704 | ELRS 420k + suppress warnings |
| `FLTMODE_CH` | 12 | Flight mode switch channel |
| `MOT_PWM_TYPE` | 4 | DShot600 |
| `SERVO_BLH_BDMASK` | 5 | Bidirectional DShot outputs 1,3 |
| `LOG_BACKEND_TYPE` | 4 | LittleFS (external flash) |
| `BATT_MONITOR` | 4 | Analog V+I |

### Tuning Parameters (Starting Points)

#### Drive Control
```
ATC_STR_RAT_P = 0.2
ATC_STR_RAT_D = 0.01
ATC_SPEED_P = 0.2
ATC_SPEED_I = 0.3
ATC_TURN_MAX_G = 0.5
```

#### Filters (High Vibration)
```
INS_GYRO_FILTER = 40
INS_ACCEL_FILTER = 20
```

#### Failsafe
```
FS_THR_ENABLE = 1
FS_THR_VALUE = 950
FS_ACTION = 2
FS_TIMEOUT = 3
```

### Complete Parameter List

Access via Mission Planner → Config → Full Parameter List

**Backup before competition:**
- Right-click parameter tree → Save to File
- Keep multiple dated backups

**Restore:**
- Right-click → Load from File

---

## Additional Resources

### Documentation
- **ArduPilot Rover:** https://ardupilot.org/rover/
- **ExpressLRS:** https://www.expresslrs.org/
- **Lua Scripting:** https://ardupilot.org/copter/docs/common-lua-scripts.html

### Community
- **ArduPilot Forums:** https://discuss.ardupilot.org/
- **Discord:** https://ardupilot.org/discord

### Development
- **GitHub:** https://github.com/ArduPilot/ardupilot
- **Wiki:** https://ardupilot.org/dev/

---

## Appendix: Quick Reference Card

```
═══════════════════════════════════════════════
         HDZERO HALO QUICK REFERENCE
═══════════════════════════════════════════════

SERIAL PORTS
  SERIAL0: USB (MAVLink)
  SERIAL1: ELRS (pre-configured, 420k)
  SERIAL2: Telemetry radio
  SERIAL4: ESC telemetry (RX only)

MOTOR OUTPUTS
  PWM1-4: PC6, PC7, PC8, PC9 (TIM3)
  BIDIR:  Outputs 1 & 3 only

FLIGHT MODES (CH12)
  Manual → Acro → Hold

FAILSAFE
  <950 PWM on throttle = Hold/Disarm

LUA SCRIPTS
  Location: @FLASH/scripts/
  Heap: 100KB (default)
  Update rate: 20-50Hz recommended

LOGGING
  Storage: 16MB SPI flash (@FLASH/logs/)
  Format: .bin tlog

BATTERY
  VBAT: PC0 (×11.0)
  CURR: PC2 (50A/V)

CALIBRATION
  1. Accel (mandatory)
  2. Compass (if external GPS)
  3. RC (verify endpoints)

═══════════════════════════════════════════════
```

---

**Last Updated:** November 2025  
**Firmware Version:** ArduPilot Rover v4.6+ (HDZERO_HALO)  
**License:** GPLv3
