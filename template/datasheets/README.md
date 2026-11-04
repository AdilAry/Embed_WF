# Datasheets

Drop PDFs for any chip/sensor/module used in this project here, then run
`/datasheet <file.pdf>` in Claude Code. It will:

1. extract the text to `<name>.txt` (with `pdftotext -layout`),
2. write a short `<name>.summary.md`: pins, voltages, bus/protocol, addresses,
   register map, timing, gotchas, with page references.

The agent reads the summary first and only goes back to the full text when needed.
That keeps its context window small.

Large vendor PDFs (>10 MB) can be kept out of git: add them to `.gitignore` and
commit only the `.txt` and `.summary.md`.
