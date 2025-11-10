# HDZero Halo Lua Examples (Combat Rover)

These examples illustrate patterns rather than complete drop-in scripts. Test in SITL first, then on hardware.

## 1) IMU-Assisted Torque Counter-Steer (Supervisory Lua)

Goal: read yaw rate and weapon RPM/current (from ESC telemetry) and bias steering to counter torque reaction.

Outline:

```lua
-- run at ~25Hz
local update_hz = 25
local last = 0

function get_yaw_rate()
  -- rad/s from AHRS gyro
  local gx, gy, gz = ahrs:get_gyro()
  return gz or 0.0
end

function get_weapon_rpm()
  -- example: read from parameter or shared variable set by a C++ module
  -- alternatively, parse ESC telemetry via SRV/RC channels depending on setup
  return param:get("WEAPON_RPM") or 0
end

function steer_bias_from_torque(yaw_rate, rpm)
  -- simple proportional estimate; tune these
  local k_yaw = 0.02
  local k_rpm = 0.0005
  return (-k_yaw * yaw_rate) + (-k_rpm * rpm)
end

function mix_outputs(bias)
  -- adjust rover turn demand around RC input
  local ch_steer = rc:get_pwm(1) -- example: CH1 steering
  local ch_throt = rc:get_pwm(3) -- example: CH3 throttle
  if not ch_steer or not ch_throt then return end

  -- convert to normalized [-1,1]
  local function norm(pwm) return (pwm - 1500) / 500 end
  local s = norm(ch_steer)
  local t = norm(ch_throt)

  local s_adj = s + bias
  if s_adj > 1 then s_adj = 1 elseif s_adj < -1 then s_adj = -1 end

  -- back to PWM and write to outputs (assign outputs appropriately)
  local function to_pwm(x) return 1500 + x * 500 end
  SRV_Channels:set_output_pwm(0, to_pwm(s_adj))  -- steering output
  SRV_Channels:set_output_pwm(1, to_pwm(t))      -- throttle output
end

function update()
  local now = millis()
  if now - last < (1000 / update_hz) then return update, 10 end
  last = now

  local yaw_rate = get_yaw_rate()
  local rpm = get_weapon_rpm()
  local bias = steer_bias_from_torque(yaw_rate, rpm)
  mix_outputs(bias)

  return update, 10
end

return update()
```

Notes:
- For sub-10ms reaction, use a small C++ module to publish a `torque_bias_yaw` parameter/var at 200–400Hz and let Lua consume it at 20–50Hz.
- Ensure outputs map to your rover setup; adjust channel numbers accordingly.

## 2) Traction Hint from ESC Current & IMU

Reduce throttle when high current coincides with little acceleration (possible stall/slip).

```lua
local last = 0
local hz = 20

function update()
  local now = millis()
  if now - last < (1000/hz) then return update, 25 end
  last = now

  -- placeholder accessors
  local current = param:get("ESC_I") or 0
  local ax, ay, az = ahrs:get_accel()
  local forward_accel = ax or 0

  if current > 20 and math.abs(forward_accel) < 0.5 then
    -- gently pull throttle back
    local t = rc:get_pwm(3) or 1500
    t = t - 20
    if t < 1100 then t = 1100 end
    SRV_Channels:set_output_pwm(1, t)
  end

  return update, 25
end

return update()
```

## 3) Mode Gate & Safety Interlock

Only apply corrections while in a specific mode and above a minimum throttle.

```lua
function active()
  -- require ACRO or MANUAL, for example
  local mode = vehicle:get_mode()
  local ACRO = 1 -- adjust to your mode table
  local MANUAL = 0
  return (mode == ACRO or mode == MANUAL) and (rc:get_pwm(3) or 1500) > 1520
end
```

## Integration Tips
- Keep scripts short; split into modules if complexity grows.
- Profile memory and CPU; start with a 100KB heap and adjust.
- When in doubt, move high-rate math to a C++ helper and surface a small number via parameter or shared binding.
