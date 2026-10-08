Zilog System 8000 cartridge tapes
=================================

zeus-3.21-install.tap   ZEUS V3.21 Operating System & Utility
                        P/N 14-0087-02 Rev. B, Cntl# 071885-B6
zeus-3.21-upgrade.tap   ZEUS 3.21 Update
                        P/N 14-0258-00 Rev. A, Cntl# 091885-AA5
sadie-3.5.tap           SADIE V3.5 Operating System & Utility
                        P/N 14-0009-09 Rev. A, Cntl# 071685-AA5

Each .tap is a SIMH tape image. The .jpg with the same name is a photo
of the original cartridge and its label.

Source
------
The cartridges belong to Mattis Lind (Stockholm, Sweden), who has owned
the Zilog S8000 Model 21 they go with since about 1988. He read them in
August 2026.

How they were read
------------------
The S8000 cartridge format is not QIC: four tracks, MFM, written by a
DEI drive with a fixed head. The tapes were read on a modified Wangtek
drive whose head is positioned by an STM32, with the read signal
captured by an FX2LP logic analyser at 24 MHz. MFM decoding and the CRC
check of every block were done in software.

Notes
-----
- Upgrade: the tape holds a single tar archive in 4,096-byte blocks.
  The image stores the same data in 10,240-byte records.
- SADIE: three of the four tracks hold data. SIMH private markers
  0x70000000 to 0x70000002 mark the start of tracks 0 to 2.

Reference
---------
VCFed forum thread "Zilog System 8000 Model 21":
https://forum.vcfed.org/index.php?threads/zilog-system-8000-model-21.1255068/
