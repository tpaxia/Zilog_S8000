-- Drive the visible MAME console through the serial bootstrap and into sawbz.
-- The tape transport remains on CPU-A TTY0; this script types only on the
-- separately attached operator-console terminal.

local keyboard = manager.machine.natkeyboard
keyboard.in_use = true

local cpu = manager.machine.devices[":slot_cpu:cpu_a:maincpu"]
local mem = cpu.spaces["program"]
local start_time = manager.machine.time:as_double()
local jumped = false
local saw_high = false
local entered_file1 = false
local probe_time = nil
local sent_boot = false
local passed = false

local function reg(name)
	local item = cpu.state[name]
	return item and item.value or 0
end

keyboard:post_coded("L SERIAL{ENTER}")
print("sawbz test: requested L SERIAL")

emu.register_periodic(function()
	local now = manager.machine.time:as_double()
	local pc = reg("PC") & 0xffff
	if not jumped and now >= start_time + 9 then
		assert(mem:read_u16(0xf000) == 0x2100, "bootstrap missing")
		keyboard:post_coded("J F000{ENTER}")
		jumped = true
		print("sawbz test: entered J F000")
	end
	if jumped and pc >= 0xf000 then
		saw_high = true
	end
	if saw_high and pc < 0x1000 then
		entered_file1 = true
	end
	if entered_file1 and not probe_time and
		(reg("R10") & 0xffff) == 0x0f00 and pc >= 0x2000 then
		probe_time = now
		print("sawbz test: RAM probe passed; waiting for Boot prompt")
	end
	if probe_time and not sent_boot and now >= probe_time + 2 then
		keyboard:post_coded("ct(0,2){ENTER}")
		sent_boot = true
		print("sawbz test: entered ct(0,2)")
	end
	if sent_boot and not passed and mem:read_u32(0x4862) == 0xdeadbabe then
		passed = true
		print(string.format("sawbz test: PASS, DEADBABE written; pc=%04x", pc))
	end
end)
