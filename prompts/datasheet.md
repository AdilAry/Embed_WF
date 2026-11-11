---
description: Extract and summarise a component datasheet PDF from datasheets/ into a compact, page-referenced summary the agent can use for drivers and libraries. Use when a new chip, sensor or module PDF is added, or before writing a driver for a part without a library.
argument-hint: <file.pdf>
---

# /datasheet — PDF → text → summary

File: `datasheets/$ARGUMENTS` (if empty, process every PDF in `datasheets/` without a `.summary.md`).

1. Extract: `pdftotext -layout datasheets/<name>.pdf datasheets/<name>.txt`.
   If the text is empty or garbage the PDF is scanned; tell the owner and ask for a text-based
   version (most vendor sites have one).
2. Read the text in chunks (search for the sections below rather than reading everything).
3. Write `datasheets/<name>.summary.md`, max ~150 lines, every fact with `(p. N)`:
   - Part number(s), variants, package
   - Supply voltage range, logic levels (is it 5 V? does it need a level shifter on the 3.3 V ESP32?),
     typical/max current
   - Interface: I2C (addresses, address pins), SPI (mode, max clock), UART (baud, framing), analog,
     1-Wire, Modbus/MBus etc.
   - Power-up / reset / init sequence and timing
   - Register map or command set actually needed for this project (table)
   - Data format and conversion formulas (scaling factors, units, signedness, endianness)
   - Error/status flags, CRC/checksum
   - Gotchas and errata
4. Check against the board: which free pins (board file §1 header table) suit this interface,
   ADC1-vs-ADC2, strapping pins, 3.3 V tolerance. Add a "Wiring proposal" section.
5. If no maintained Arduino library exists (check Library Manager with `arduino-cli lib search`),
   say so and recommend writing a small driver: register/frame decoding in `firmware/src/logic/`
   (host-testable with example values from the datasheet), bus access in `firmware/src/hal/`.
6. Commit the `.txt` and `.summary.md`. Mention if the PDF is large (>10 MB) and should be git-ignored.
