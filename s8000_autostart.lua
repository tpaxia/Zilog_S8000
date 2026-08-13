-- Press the System 8000 front-panel START button.
--
-- MAME runs this file after -autoboot_delay seconds.  Use a delay of 2 to
-- reproduce a numeric-keypad '+' press two seconds after machine startup:
--
--   -autoboot_delay 2 -autoboot_script s8000_autostart.lua

local frontpanel = assert(
	manager.machine.ioport.ports[":FRONTPANEL"],
	"S8000 front-panel input port not found")
local start = assert(frontpanel.fields["Start"], "S8000 START input not found")

-- Hold START across several complete input frames, then return control to the
-- normal input system.  Releasing at the first frame-done callback is too
-- early: it can occur before MAME's next input poll observes the assertion.
-- This drives the same IPT_START field as numeric-keypad '+'.
start:set_value(1)

local frames_left = 6
emu.register_frame_done(function()
	if frames_left > 0 then
		frames_left = frames_left - 1
	end
	if frames_left == 0 then
		start:set_value(0)
		start:clear_value()
		frames_left = -1
	end
end)
