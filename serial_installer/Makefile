AS      := z8k-coff-as
LD      := z8k-coff-ld
OBJCOPY := z8k-coff-objcopy
PYTHON  := python3
BUILD   := build

TAPE := ../tapes/images/zeus-3.21-install.tap
PATCHED  := $(BUILD)/sarestor-serial.bin
LOADER_PATCHED := $(BUILD)/loader-serial.bin
PRIMARY_PATCHED := $(BUILD)/primary-serial.bin

.PHONY: all test clean

all: $(PATCHED) $(LOADER_PATCHED) $(PRIMARY_PATCHED) $(BUILD)/bootstrap.bin

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/serial_ct.o: serial_ct.s | $(BUILD)
	$(AS) -o $@ $<

$(BUILD)/serial_ct.elf: $(BUILD)/serial_ct.o
	$(LD) -e 0 -Ttext 0 -o $@ $<

$(BUILD)/serial_ct.bin: $(BUILD)/serial_ct.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@

$(BUILD)/bootstrap.o: bootstrap.s | $(BUILD)
	$(AS) -o $@ $<

$(BUILD)/bootstrap.elf: $(BUILD)/bootstrap.o bootstrap.ld
	$(LD) -T bootstrap.ld -o $@ $<

$(BUILD)/bootstrap.bin: $(BUILD)/bootstrap.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@

$(BUILD)/primary_serial.o: primary_serial.s | $(BUILD)
	$(AS) -o $@ $<

$(BUILD)/primary_serial.elf: $(BUILD)/primary_serial.o
	$(LD) -e 0 -Ttext 0 -o $@ $<

$(PRIMARY_PATCHED): $(BUILD)/primary_serial.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@
	@test $$(wc -c < $@) -le 512

$(PATCHED): patch_sarestor.py serve_tape.py $(BUILD)/serial_ct.bin $(TAPE)
	$(PYTHON) patch_sarestor.py $(TAPE) $(BUILD)/serial_ct.bin $@

$(LOADER_PATCHED): patch_loader.py serve_tape.py $(BUILD)/serial_ct.bin $(TAPE)
	$(PYTHON) patch_loader.py $(TAPE) $(BUILD)/serial_ct.bin $@

test: all
	$(PYTHON) -m unittest -v test_protocol.py

clean:
	rm -rf $(BUILD) __pycache__
