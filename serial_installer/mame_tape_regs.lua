-- Report the register contract established by the monitor's real ZT path.
local keyboard = manager.machine.natkeyboard
keyboard.in_use = true
local cpu = manager.machine.devices[":slot_cpu:cpu_a:maincpu"]
local start_time = manager.machine.time:as_double()
local next_report = start_time
emu.register_periodic(function()
	local now = manager.machine.time:as_double()
	if now >= next_report then
		print(string.format(
			"tape regs: t=%.1f pc=%04x r4=%04x r5=%04x r7=%04x fcw=%04x",
			now, cpu.state["PC"].value & 0xffff,
			cpu.state["R4"].value & 0xffff,
			cpu.state["R5"].value & 0xffff,
			cpu.state["R7"].value & 0xffff,
			cpu.state["FCW"].value & 0xffff))
		next_report = next_report + 0.25
	end
end)
