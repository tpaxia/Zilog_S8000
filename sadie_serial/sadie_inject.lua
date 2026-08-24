-- Place a SADIE diagnostic directly in memory instead of loading it from tape.
--
-- The SADIE 3.5 executive loads a diagnostic to physical segment 0, offset
-- 0x9000, and enters it with `call %9000` through the thunk at 0x033e.  Before
-- loading it compares the selected test's track and file against its current
-- tape position in 0x4936 and 0x4938; when they already match it skips the
-- load and runs whatever is at 0x9000 (executive 0x14c0..0x14dc).
--
-- Restoring a save state taken at COMMAND LEVEL and priming those two words is
-- therefore enough: the operator selects the test as usual and the executive's
-- own code populates the parameter block, prints the name, and keeps the pass
-- and error counts.  Nothing here forces a PC or a register.
--
-- The state is loaded from Lua rather than with MAME's -state option, and the
-- injection runs from a post-load notifier.  Loading a state discards MAME's
-- pending timers and every Lua periodic callback with them, so -state stops the
-- autoboot script from ever running and emu.wait() never returns.  The post-load
-- notifier is the one hook that survives, and it also fires exactly when the
-- restored memory is in place.
--
-- Environment:
--   SADIE_IMAGE   diagnostic image to inject (required)
--   SADIE_STATE   save state to restore (default sadie-cmdlevel)
--   SADIE_TRACK   track the executive believes is loaded (default 1)
--   SADIE_FILE    logical file the executive believes is loaded (required)
--   SADIE_CPU     CPU tag (default :slot_cpu:cpu_a:maincpu)

local LOAD_BASE = 0x9000
local LOAD_LIMIT = 0x6d60       -- executive 0x14f8: maximum total byte count
local CUR_TRACK = 0x4936
local CUR_FILE = 0x4938
local DRIVER_SIGNATURE = 0x030f -- sadie_tape_serial.bin word 0, linked at 0x2874

local function number(name, default)
	local text = os.getenv(name)
	return text and assert(tonumber(text), name .. " is not a number") or default
end

local image_path = assert(os.getenv("SADIE_IMAGE"), "sadie-inject: SADIE_IMAGE is not set")
local state = os.getenv("SADIE_STATE") or "sadie-cmdlevel"
local track = number("SADIE_TRACK", 1)
local file_number = assert(number("SADIE_FILE", nil), "sadie-inject: SADIE_FILE is not set")
local cpu_tag = os.getenv("SADIE_CPU") or ":slot_cpu:cpu_a:maincpu"

local handle = assert(io.open(image_path, "rb"),
	"sadie-inject: cannot open " .. image_path)
local image = handle:read("a")
handle:close()
assert(#image > 0 and #image <= LOAD_LIMIT, string.format(
	"sadie-inject: %s is %d bytes; the executive accepts at most %d",
	image_path, #image, LOAD_LIMIT))

local function inject()
	local cpu = assert(manager.machine.devices[cpu_tag],
		"sadie-inject: no CPU at " .. cpu_tag)
	local program = assert(cpu.spaces["program"], "sadie-inject: no program space")
	local data = cpu.spaces["data"]

	local signature = program:read_u16(0x2874)
	assert(signature == DRIVER_SIGNATURE, string.format(
		"sadie-inject: 0x2874 reads %04x, expected the serial driver's %04x -- " ..
		"the save state did not restore SADIE", signature, DRIVER_SIGNATURE))

	-- Clear the whole window first so a short diagnostic never inherits the
	-- tail of whichever one was loaded when the save state was taken.
	for offset = 0, LOAD_LIMIT - 1 do
		program:write_u8(LOAD_BASE + offset, 0)
	end
	for offset = 1, #image do
		program:write_u8(LOAD_BASE + offset - 1, image:byte(offset))
	end

	-- Read back through both spaces.  The executive is a flat non-segmented
	-- image running at logical zero, so segment 0 is expected to map straight
	-- through; if it does not, or if code and data mappings disagree, say so
	-- and stop rather than run a diagnostic that was never really written.
	for _, probe in ipairs({0, 1, 2, #image // 2, #image - 2, #image - 1}) do
		local want = image:byte(probe + 1)
		local got = program:read_u8(LOAD_BASE + probe)
		assert(got == want, string.format(
			"sadie-inject: program readback at %04x is %02x, expected %02x",
			LOAD_BASE + probe, got, want))
		if data then
			local seen = data:read_u8(LOAD_BASE + probe)
			assert(seen == want, string.format(
				"sadie-inject: data readback at %04x is %02x, expected %02x",
				LOAD_BASE + probe, seen, want))
		end
	end

	-- Make the executive believe the tape already sits on this track and file.
	program:write_u16(CUR_TRACK, track)
	program:write_u16(CUR_FILE, file_number)
	assert(program:read_u16(CUR_TRACK) == track and
		program:read_u16(CUR_FILE) == file_number,
		"sadie-inject: tape position words did not take")

	print(string.format(
		"sadie-inject: %s, %d bytes at %04x, posing as track %d file %d",
		image_path, #image, LOAD_BASE, track, file_number))
	print("sadie-inject: ready")
end

-- Held in a global on purpose: the subscription unsubscribes when collected.
_G.sadie_inject_subscription = emu.add_machine_post_load_notifier(inject)

local requested = false
emu.register_periodic(function()
	if not requested and manager.machine.time:as_double() >= 1.0 then
		requested = true
		print("sadie-inject: restoring save state " .. state)
		manager.machine:load(state)
	end
end)
