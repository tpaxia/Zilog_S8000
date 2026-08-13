-- Test monitor download -> serial bootstrap -> file 0 -> file 1.
-- This deliberately uses MAME's default serial terminal on console channel B
-- and never sends an installer command after file 1 starts.

local keyboard = manager.machine.natkeyboard
keyboard.in_use = true

local stopbits = assert(manager.machine.ioport.ports[
	":slot_cpu:cpu_a:sio0:cha:tty0:null_modem:RS232_STOPBITS"])
assert(stopbits:read() == 3, "configure TTY0 for two stop bits")
assert(manager.machine.ioport.ports[":slot_cpu:cpu_a:SEGJP"]:read() == 1,
	"enable CPU-A Support Segmented OS")

for tag, _ in pairs(manager.machine.devices) do
	assert(not tag:find(":h19:", 1, true), "H19 must not be instantiated")
end

local cpu = manager.machine.devices[":slot_cpu:cpu_a:maincpu"]
local mem = cpu.spaces["program"]
local start_time = manager.machine.time:as_double()
local jumped = false
local saw_relocated_loader = false
local entered_file1 = false
local passed_probe = false

keyboard:post_coded("L SERIAL{ENTER}")
print("downloader test: requested monitor L SERIAL; no H19 instantiated")

emu.register_periodic(function()
	local now = manager.machine.time:as_double()
	local pc = cpu.state["PC"].value & 0xffff
	if not jumped and now >= start_time + 9 then
		assert(mem:read_u16(0xf000) == 0xa17a,
			"bootstrap signature missing at f000")
		keyboard:post_coded("J F000{ENTER}")
		jumped = true
		print("downloader test: bootstrap present; entered J F000")
	end
	if jumped and pc >= 0xf000 then
		saw_relocated_loader = true
	end
	if saw_relocated_loader and not entered_file1 and pc < 0x1000 then
		entered_file1 = true
		assert(mem:read_u16(0x38bc) == 0xa5a5,
			"patched RAM-probe pattern missing at 38bc")
		print(string.format("downloader test: file 1 entered at pc=%04x", pc))
	end
	if entered_file1 and not passed_probe and
			(cpu.state["R10"].value & 0xffff) == 0x0f00 and pc >= 0x2000 then
		passed_probe = true
		print(string.format(
			"downloader test: PASS, RAM probe ended at r10=0f00; pc=%04x", pc))
	end
end)
