-- HDZero Halo Lua Memory & Performance Profiler
-- Drop this file into @FLASH/scripts/mem_prof.lua
-- Emits periodic STATUSTEXT messages with Lua heap usage, free RAM, and execution time.

local hz = 2                 -- update frequency (Hz)
local min_interval_ms = 1000 / hz
local last = 0
local seq = 0

-- optional: set to true to include per-script CPU timing
local measure_cpu = true

local function fmt(bytes)
  if bytes < 1024 then return string.format("%dB", bytes) end
  return string.format("%.1fKB", bytes / 1024)
end

local function send(text)
  -- severity 6 (INFO)
  gcs:send_text(6, text)
end

local function update()
  local now = millis()
  if now - last < min_interval_ms then
    return update, 50 -- sleep short; scheduler revisits later
  end
  last = now
  seq = seq + 1

  local start_us
  if measure_cpu then
    start_us = micros()
  end

  -- Lua heap usage in KB (collectgarbage returns kilobytes)
  local lua_kb = collectgarbage("count")
  -- Free RAM (bytes) if hal.mem_free() is available; fallback if not
  local free_bytes = 0
  if hal and hal.mem_free then
    free_bytes = hal.mem_free()
  end

  if measure_cpu then
    local elapsed_us = micros() - start_us
    send(string.format(
      "LuaProf #%d heap=%.1fKB free=%s cpu=%dus", seq, lua_kb, fmt(free_bytes), elapsed_us))
  else
    send(string.format(
      "LuaProf #%d heap=%.1fKB free=%s", seq, lua_kb, fmt(free_bytes)))
  end

  -- Perform a light incremental collection occasionally (every 30 samples)
  if seq % 30 == 0 then collectgarbage("step", 64) end

  return update, 500 -- next call in ~0.5s; scheduler adjusts
end

return update()
