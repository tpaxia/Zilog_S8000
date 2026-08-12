# Rebuild the System 8000 CPU-A monitor 3.0 EPROMs from source.
#
#   make            assemble monitor30.s -> build/monitor30.bin
#   make verify     prove the rebuild matches the original EPROMs byte for byte
#   make gen        regenerate monitor30.s from the image + regions.txt
#   make eproms     split the rebuilt image back into the four 2732 files

AS       := z8k-coff-as
LD       := z8k-coff-ld
OBJCOPY  := z8k-coff-objcopy
OBJDUMP  := z8k-coff-objdump
PYTHON   := python3

ROMDIR   := ../../roms
REF      := monitor30.bin
SRC      := monitor30.s
BUILD    := build

.PHONY: all verify gen eproms trace audit pointers clean

all: $(BUILD)/monitor30.bin

# Reference image: the four EPROMs interleaved into one big-endian 16 KB blob.
$(REF): tools/rom.py $(ROMDIR)/cpu_34-0715-03a.u76
	$(PYTHON) tools/rom.py join $(ROMDIR) $@

# Symbol references inside .text still carry COFF relocations, so the object
# has to be linked at its ROM address (0) before the image is extracted.
$(BUILD)/monitor30.bin: $(SRC) | $(BUILD)
	$(AS) -o $(BUILD)/monitor30.o $(SRC)
	$(LD) -e 0 -Ttext 0 -o $(BUILD)/monitor30.elf $(BUILD)/monitor30.o
	$(OBJCOPY) -O binary --only-section=.text --pad-to 0x4000 --gap-fill 0xff $(BUILD)/monitor30.elf $@
	@size=$$(wc -c < $@); \
	 if [ $$size -gt 16384 ]; then \
	   echo "error: image is $$size bytes; the four 2732s hold 16384"; \
	   rm -f $@; exit 1; \
	 fi

$(BUILD):
	mkdir -p $(BUILD)

verify: $(BUILD)/monitor30.bin $(REF)
	@if cmp -s $(BUILD)/monitor30.bin $(REF); then \
	  echo "OK: rebuilt image is identical to the original EPROM set"; \
	else \
	  echo "MISMATCH:"; cmp -l $(BUILD)/monitor30.bin $(REF) | head -40; exit 1; \
	fi

ANNOT := regions.txt seeds.txt escapes.txt equates.txt annotations.txt pointers.txt

gen: $(REF) $(ANNOT)
	$(PYTHON) tools/gen.py $(REF) $(ANNOT) > $(SRC).new
	mv $(SRC).new $(SRC)

trace: $(REF)
	$(PYTHON) tools/trace.py $(REF) seeds.txt

pointers: $(REF)
	@echo '# candidates -- merge into pointers.txt by hand'
	$(PYTHON) tools/pointers.py $(REF) seeds.txt regions.txt

audit: $(REF)
	$(PYTHON) tools/audit.py $(REF) regions.txt

eproms: verify
	$(PYTHON) tools/rom.py split $(BUILD)/monitor30.bin $(BUILD)/eproms
	@cd $(BUILD)/eproms && shasum *

clean:
	rm -rf $(BUILD) $(SRC).new
