AS      := z8k-coff-as
LD      := z8k-coff-ld
OBJCOPY := z8k-coff-objcopy
BUILD   := build
PYTHON  := python3
TAPE    := ../tapes/images/sadie-3.5.tap

.PHONY: all clean test

all: $(BUILD)/sadie_tape_serial.bin $(BUILD)/sadie_primary_serial.bin \
	$(BUILD)/sadie-executive-serial.bin

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/sadie_tape_serial.o: sadie_tape_serial.s ../serial_installer/xmodem_receive.inc | $(BUILD)
	$(AS) -o $@ $<

$(BUILD)/sadie_tape_serial.elf: $(BUILD)/sadie_tape_serial.o
	$(LD) -e 0x2874 -Ttext 0x2874 -o $@ $<

$(BUILD)/sadie_tape_serial.bin: $(BUILD)/sadie_tape_serial.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@
	@test $$(wc -c < $@) -eq 1218

$(BUILD)/sadie_primary_serial.o: sadie_primary_serial.s | $(BUILD)
	$(AS) -o $@ $<

$(BUILD)/sadie_primary_serial.elf: $(BUILD)/sadie_primary_serial.o
	$(LD) -e 0 -Ttext 0 -o $@ $<

$(BUILD)/sadie_primary_serial.bin: $(BUILD)/sadie_primary_serial.elf
	$(OBJCOPY) -O binary --only-section=.text $< $@
	@test $$(wc -c < $@) -le 512

$(BUILD)/sadie-executive-serial.bin: patch_executive.py serve_sadie.py \
	$(BUILD)/sadie_tape_serial.bin $(TAPE)
	$(PYTHON) patch_executive.py $(TAPE) $(BUILD)/sadie_tape_serial.bin $@

test: all
	$(PYTHON) -m unittest -v test_sadie.py

clean:
	rm -rf $(BUILD)
