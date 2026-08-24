-- Save a MAME state once SADIE is loaded and sitting at COMMAND LEVEL.
--
-- Whether SADIE has finished starting is visible on the operator console, not
-- in memory: the executive's bytes arrive well before it has read its own
-- configuration off track 2 and printed the menu.  So make_snapshot.py watches
-- the console and creates a trigger file, and this script saves when it appears.
-- Waiting a fixed time instead saves a state mid-startup, with a tape read in
-- flight that no later run can resynchronise.
--
-- Environment:
--   SADIE_TRIGGER          file to wait for before saving (required)
--   SADIE_STATE            state name to write (default sadie-cmdlevel)
--   SADIE_CPU              CPU tag (default :slot_cpu:cpu_a:maincpu)
--   SADIE_LOAD_TIMEOUT     seconds to wait for the trigger (default 1800)

local DRIVER_SIGNATURE = 0x030f -- sadie_tape_serial.bin word 0, linked at 0x2874
local FINAL_RECORD = 0x6800     -- first word of the executive's last record
local FINAL_SIGNATURE = 0x6e20

local function number(name, default)
	local text = os.getenv(name)
	return text and assert(tonumber(text), name .. " is not a number") or default
end

local trigger = assert(os.getenv("SADIE_TRIGGER"), "SADIE_TRIGGER is not set")
local state = os.getenv("SADIE_STATE") or "sadie-cmdlevel"
local cpu_tag = os.getenv("SADIE_CPU") or ":slot_cpu:cpu_a:maincpu"
local timeout = number("SADIE_LOAD_TIMEOUT", 1800)

local cpu = assert(manager.machine.devices[cpu_tag], "no CPU at " .. cpu_tag)
local program = assert(cpu.spaces["program"], "no program space")

local function exists(path)
	local handle = io.open(path, "r")
	if handle then
		handle:close()
		return true
	end
	return false
end

print("sadie-snapshot: waiting for COMMAND LEVEL")
local waited = 0
local announced = false
while waited < timeout do
	if not announced and program:read_u16(0x2874) == DRIVER_SIGNATURE and
			program:read_u16(FINAL_RECORD) == FINAL_SIGNATURE then
		print(string.format(
			"sadie-snapshot: executive loaded after %d seconds", waited))
		announced = true
	end
	if exists(trigger) then
		break
	end
	emu.wait(1)
	waited = waited + 1
end
assert(waited < timeout, string.format(
	"sadie-snapshot: no COMMAND LEVEL after %d seconds", timeout))

manager.machine:save(state)
emu.wait(2)
print("sadie-snapshot: saved " .. state)
print("sadie-snapshot: ready")
