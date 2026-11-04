---
name: define
description: Turn the rough idea in docs/IDEA.md into a complete, testable Functional Specification (docs/FSD.md) by interviewing the owner one question at a time, then propose an implementation plan (docs/PLAN.md). Use when starting a project or when the FSD is still the empty template.
argument-hint: "[optional extra context]"
---

# /define — idea → FSD → plan

Extra context from the owner: $ARGUMENTS

You are a patient embedded systems engineer interviewing a **beginner**. Your job is to
produce `docs/FSD.md` in the structure already in that file, where **every requirement is
testable and names the fastest test tier that can prove it**.

## Steps

1. Read `docs/IDEA.md`, `docs/FSD.md` (template/structure), `docs/hardware/*.md` and any
   `datasheets/*.summary.md`. If IDEA.md is still the empty template, ask the owner to describe
   the idea in a few sentences first.

2. Make a private list of what is unknown. Typical gaps for this board:
   which touch variant(s) must work (default: both); screen layout; Wi-Fi? (how are credentials
   entered: captive portal / serial / compile-time); MQTT or Home Assistant; BLE; external sensors
   and which free pins (only from the board file's header table, flag ADC2/strapping pins);
   power (USB / LiPo); persistence (NVS); OTA (needs `PartitionScheme=default`);
   behaviour on errors (Wi-Fi lost, broker down, sensor missing, bad input);
   what "done" means for the owner.

3. Interview: **ask ONE question per message**, most important first. Offer 2–4 concrete options
   with a recommended default so a beginner can just pick. Explain jargon in one short clause.
   Stop asking when the remaining gaps can be filled with sensible defaults — list those defaults
   for the owner to confirm in one go. Aim for 5–12 questions, not 30.

4. Write `docs/FSD.md`:
   - Requirements table: `REQ-xxx` IDs (step by 10 so later ones can be inserted), one testable
     sentence each, Tier (`host` / `target` / `bench` / `field` / `manual`), Test name.
     Keep the template's baseline rows REQ-001…006 unless the owner drops that feature.
   - Name the tests now, even though they don't exist yet: host `snake_case` names (wildcards
     like `mbus_*` allowed), target `T-XXXX` IDs, bench `test_req_<nnn>_<what>` functions.
     No `|` inside a table cell (it breaks the table).
   - Prefer `host` for anything that is pure logic (parsing, formatting, state machines, maths) —
     that tells the implementation to put it in `firmware/src/logic/`.
   - Include negative / fault-injection requirements (§4.1). They are as important as happy paths.
   - Explicit **Out of scope** list.
   - Open questions you could not resolve.
   - Change log entry `0.1`.

5. Show the owner a short summary (requirement count per tier, key decisions, defaults you chose)
   and ask for corrections. Iterate until they say it's OK, then set Status = agreed.

6. Write `docs/PLAN.md`: keep Phase 0 (commissioning) as is, then split the requirements into
   small phases (each finishable in one session, each ending with green tests). Every plan item
   names the REQ IDs it covers.

7. Run `make trace`. The new requirements show `NO TEST` — that is the to-do list for
   `/build-loop`. Fix anything shown as `BAD TIER` or a duplicate ID.
   `git add docs && git commit -m "FSD v0.1 and plan"`. Tell the owner the next step is
   `/commission` (with a board plugged into the dev box).

Never write firmware in this skill.
