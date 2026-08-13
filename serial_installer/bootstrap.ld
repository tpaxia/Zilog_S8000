OUTPUT_FORMAT("coff-z8k")
OUTPUT_ARCH("z8002")
ENTRY(_start)

SECTIONS
{
  .text 0xf000 : { *(.text) }
}
