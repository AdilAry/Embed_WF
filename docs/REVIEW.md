# Review history of the Embed_WF kit

Ten passes so far. The newest is first. None of them has touched your real
boards or the T480s, so the last section is the list that matters most.

## Pass 10 (November 2026): the dev box moves to Debian 13

Session 3 of 3. The T480s runs Debian 13.7 (trixie) with KDE Plasma instead of
Linux Mint, before its first run. The contract date stays 21 November 2026:
WORKFLOW.md §9 says the 22 November change (competition material leaves the
core) doesn't touch this kit.

| # | Change | Why |
|---|---|---|
| 1 | `setup-root.sh` adds `/usr/sbin` to its PATH, and says to use `su -` when your account has no sudo | Debian's plain `su` keeps your PATH without `/usr/sbin`: `adduser` and `usermod` would not be found. With a root password set at install, your account gets no sudo. |
| 2 | Packages add `dnsmasq-base`, `wpasupplicant` (the hotspot), `avahi-daemon`, `libnss-mdns` (`<hostname>.local`), `pciutils`; `adduser --gecos` becomes `--comment` | Debian only recommends the first two; the script's closing message relies on mDNS; `--gecos` is now an old alias. |
| 3 | New step 6: installs `firmware-iwlwifi` when the Intel card has none (or says how to enable non-free-firmware), and warns if NetworkManager sees no Wi-Fi device, or one that is `unmanaged` or `unavailable` | `bench-wifi` needs NetworkManager in charge of the card, and the 8265's Bluetooth firmware is in the same package. The branches were run against stub commands, not on a real Debian. |
| 4 | New step 9: `/etc/systemd/logind.conf.d/50-embwf-lid.conf` with `HandleLidSwitchExternalPower=ignore`, active after a reboot | KDE's lid setting holds only while someone is logged in to Plasma; over SSH with nobody logged in, logind would suspend. The script doesn't restart logind, which could end the running desktop session. |
| 5 | The `.pkla` polkit file is no longer written; only the JS rule | Debian 13's polkit doesn't read `.pkla` files, and Mint is no longer a target. |
| 6 | GUIDE B1/B2 (install choices, sudo, update, lid), the diagram, README, AGENTS.md, `machines.md`, troubleshooting (Wi-Fi device, `rfkill` path, lid) say Debian | `brltty` is still removed if present: harmless where it isn't installed. |

Also since pass 9: GUIDE §7 and the cheatsheet point to WORKFLOW.md §4 ("Watch
the context") for when to wrap, instead of restating "40%", which workflow v2.9
dropped.

## Pass 9 (November 2026): contract of 21 November 2026

The workflow's §8 contract moved to 21 November. Nothing in the kit broke: the
new "At /judge also" fields are optional, the git commands are unchanged, and
the template has none of the fields that switch on `/judge`'s competition steps.

| # | Change | Why |
|---|---|---|
| 1 | README names the contract of 21 November 2026 | The date line. |
| 2 | GUIDE §5 no longer says how `/judge` ranks issues; it points to WORKFLOW.md §5 | It described the old "value per hour", and how a workflow command works inside. |
| 3 | `template/PROGRESS.md` "How to run" starts with a `Needs:` line: the dev box after both setup scripts; for `make loop`, the boards registered and on USB | `/judge` step 2 would have counted the dev box, the boards and flashing as issues in every pass. The fix landed in the workflow: the setup "How to run" says a machine needs is expected. **An existing project adds this `Needs:` line by hand.** |

## Pass 8 (November 2026): Claude Code is the agent, pi is for later

Session 2 of 3. pi stays possible for the day the owner can host models, but
nothing presents it as the default any more.

| # | Change | Why |
|---|---|---|
| 1 | `devbox/setup-user.sh` installs Claude Code instead of pi, and checks `WORKFLOW_DIR` before anything else | One run: clone the workflow, run its `install.sh`, open a new terminal, run `setup-user.sh`. No 1 GB download before a missing prerequisite is found. |
| 2 | `template/.claude/settings.json`: an allowlist modelled on Gamedev_WF's, so both kits handle permissions the same way. Allowed: `make`, the two tools, read-only `arduino-cli` and `gh run`, the git commands WORKFLOW.md §8 lists (contract of 20 Nov 2026: `pull`, `status`, `add`, `commit`, `show --stat`, `push`), plus the read-only `diff` and `log` that §8 allows a kit to add. Denied: `sudo`, force-push, `git reset --hard`, edits under `build/` and to `build_id.h` | Without it every `make` waits for approval, which ends the loop. Built from the §8 line, so a session never waits on a prompt the workflow causes; when that line changes, so does this list. Other git commands (branches, anything that rewrites history) still ask. The `build/` deny turns the "evidence is never edited by hand" rule into a lock for the edit tools. CI checks the file is valid JSON. |
| 3 | GUIDE §6 rewritten: the allowlist runs the loop, the account is still the wall | `make` runs whatever the Makefile says, and the agent may edit the Makefile. The list is a convenience, not a lock. |
| 4 | README, GUIDE, cheatsheet, troubleshooting, planning-chat, machines.md, `new_project.sh`, `/new-project`: Claude Code commands (`claude`, `/clear`, `Esc Esc`, `/context`, `claude -c`) instead of pi's | pi facts stay where they are labelled "later". |
| 5 | GUIDE Part A: the Windows line for the kit's commands (`Copy-Item prompts\*.md ...`), as WORKFLOW.md §8 gives it | For Claude Code on the Legion; boards are still flashed from the dev box only. |
| 6 | The kit's docs and prompts no longer describe how `/start` and `/wrap` work inside. The cheatsheet and GUIDE §5 point to WORKFLOW.md §4; troubleshooting drops three rows WORKFLOW.md §7 already has; `/define`, `/commission` and `/change-request` say what "Next" and the history entry must hold, not what `/wrap` does | Only the §8 contract words are used. |

## Pass 7 (November 2026): the workflow becomes an external dependency

The short-loop workflow now lives in its own repository. This kit no longer
carries a copy of it: it finds the workflow through `WORKFLOW_DIR` (set by the
workflow's installer) and relies only on its WORKFLOW.md §8 contract (then dated
19 November 2026; now 20 November). Session 1 of 3; sessions 2 (Claude Code as the agent, pi for
later) and 3 (Debian on the dev box, if chosen) follow.

| # | Change | Why |
|---|---|---|
| 1 | `workflow/`, `tools/build-workflow-zip.sh` and the CI steps that checked them are gone | The copy had already fallen behind the workflow (the stop rule for changed tests, ticking only plans with checkboxes). The checks on this kit's own files stay. |
| 2 | `tools/install-workflow.sh` and `devbox/setup-user.sh` stop with a clear message if `WORKFLOW_DIR` isn't set; they never guess a path. `new-project` on the dev box is a link to the workflow's own generator | One variable, set in one place. `new_project.sh --generic` is gone: it only forwarded to that generator. |
| 3 | `template/AGENTS.md` no longer restates the loop or its stop rules. It keeps only embedded facts: one plan item per task, the test-tier order, `STALE`, physical actions, spec changes via `/change-request`, the flashing rule | The restated copy had already missed the rule against editing a test to get green. "Never weaken a test" in Rules went for the same reason: `/start` has it. |
| 4 | Repo `AGENTS.md`, README, GUIDE, cheatsheet, troubleshooting point to the external workflow | The README names the contract date. |

Found here and fixed in workflow v2 (20 Nov): its `install.sh`
exited before saving `WORKFLOW_DIR` when no agent was installed yet, which would
have made a fresh dev-box account run `setup-user.sh` twice. With the fix it runs
once: clone the workflow, run its `install.sh`, open a new terminal, then
`setup-user.sh` (pass 8).

## Pass 6 (November 2026): five points on the standalone workflow

| # | Point | Verdict | What was done |
|---|---|---|---|
| 1 | The bracket check could never come back empty: the lines explaining the IF marker contained one | Agree; my bug | Both lines reworded. CI now fails if the instruction lines of the starter contain a bracket. |
| 2 | Two copies of `/start`, `/wrap`, `/judge` (kit and standalone) | Premise out of date, conclusion right | Since pass 5 the kit has only the embedded commands and installs the generic ones from `workflow/`. What remains is `workflow/` here versus an unzipped copy elsewhere. Making the workflow its own repository, and dropping `workflow/` from this kit, is the fix; it waits on the owner creating that repository. |
| 3 | The Run limit only counted failed runs of "done when" | Agree on the loophole, not on the fix | Counting every *failed* run would stop healthy test-first sessions, where each step starts with a run that is meant to fail. The limit now counts every test or build run, passed or failed: 20 in the generic starter, 25 here (host tests are run often). The earlier exemption for `make host-test` was the same loophole and is gone. Both numbers are starting points to tune. |
| 4 | `PROGRESS.md` carried an optional Time section the bracket check doesn't cover | Agree, simpler fix | The table is no longer in the template. The Competition section creates it the first time it logs a start time, so a normal project has nothing to delete. |
| 5 | `efficient-ai-tools.md` called pi "shelved for later" | Agree | Reworded to "second agent"; the section is now "Pi", with local models marked as later. |

## Pass 5 (November 2026): workflow v3, and an outside review

Your revised template (modes removed, "done when", the run limit, owner checks)
and eleven review points from an outside chat were merged. The generic workflow
now lives in one folder, `workflow/`, which is also shipped as a standalone zip;
the embedded layer builds on it.

| # | Review point | Verdict | What was done |
|---|---|---|---|
| 1 | Learn mode can't coexist with a loop that runs until "done when" passes | Agree | Modes removed everywhere. Teaching is a per-task request with its own "done when" (WORKFLOW §8). |
| 2 | No limit on context: add a stop after 10 runs without a pass | Agree, with one change | **Run limit** in each project's AGENTS.md, default 10. In embedded projects it counts flash-and-test runs, not `make host-test`, which is cheap and should run often. A count is only a proxy: one huge log costs more than ten quiet runs, so "look, don't dump" stays. |
| 3 | The competition profile lost its time tracking | Agree; the cause was mine | Splitting the competition parts into a paste-in profile separated the rule from the commands that did the work. Profiles are gone: one template again, with `Competition` as a whole optional section that carries its own "At /start also" and "At /wrap also" steps. |
| 4 | `/wrap` marks items done before you've checked them | Agree, extended | Items with a check only you can do stay "awaiting my check"; the next `/start` asks and records it. Not adopted: holding back the push. Pushing is not finishing, CI on the push is one of the checks, and nothing is deployed. |
| 5 | Flashing without asking when the board drives something physical | Agree, per session not per upload | FSD §3 records whether the board drives anything that can move, heat, switch mains or charge a battery; `/define` always asks. If so, the plan says the session flashes and waits for your OK once. An OK per upload would end the loop. |
| 6 | "Done when" for tasks with no code | Agree | A file, what it must say, and your approval. Never an invented check. |
| 7 | Symlink the commands on Linux | Agree, with a fallback | Links are the default: pi's loader follows linked files (checked in its source). Claude Code's docs don't say, so `--copy` exists. The user-level file is still copied, never linked: it is yours to edit. Side effect to know: switching the kit to another branch changes the live commands. |
| 8 | `history.md` still asks for time spent | Agree | Dropped; the `Competition` section adds it. |
| 9 | pi does read `CLAUDE.md` | Agree; I had it wrong | Per folder pi loads one of `AGENTS.override.md`, `AGENTS.md`, `CLAUDE.md`, in that order. Wording fixed here and in the workflow guide. It weakens one of my earlier arguments for `AGENTS.md`, not the conclusion. |
| 10 | pi loads parent folders' files too | Agree, as a check not a note | Both project generators refuse to create a project under a folder that has its own instruction file. |
| 11 | The shim might make Claude Code load `AGENTS.md` twice | Disagree | Claude Code's docs say the import never causes a second read, and when both files exist only `CLAUDE.md` is read. From v2.1.277 `AGENTS.md` alone also works. The shim stays; `/context all` shows what was loaded. |

## Pass 4 (November 2026): the short loop

Your generic short-loop workflow (short sessions, files as memory, `/start` …
`/wrap`, `/judge` in a fresh session) was reviewed and made the way every
project in this kit is worked. The embedded workflow changed shape to fit it.

| # | Finding | Why it matters | Change |
|---|---|---|---|
| 1 | The embedded kit ran long: `/build-loop` implemented a whole phase with no plan approval, the opposite of a short loop. | Long sessions cost more per step as context fills, and your only gates were physical actions and failures. | `/build-loop` and `/wrap-up` are gone. One plan item per session: `/start` proposes a plan and waits, the agent loops against the tests inside it, `/wrap` ends it. The closed test loop is still there, just bounded. |
| 2 | The embedded kit had no current-state file. `docs/NOTES.md` was an append-only log the agent was pointed at every session. | That is the growing-file problem your workflow was written to fix. | `PROGRESS.md` (snapshot, rewritten every `/wrap`), `docs/history.md` (append-only, read on request) and `docs/decisions.md` replace `NOTES.md`. |
| 3 | The short-loop workflow was set up for Claude Code only (`.claude/commands/` per project, `~/.claude/CLAUDE.md`). | pi does read a project's `CLAUDE.md`, but not the user-level file or the commands. | `AGENTS.md` is the instruction file, `CLAUDE.md` a one-line shim. One set of command files serves both agents; `tools/install-workflow.sh` installs it and the user-level file per machine. |
| 4 | The project template was shaped by a hackathon data app; other project types had to delete most of it. | "Applies to most software work" by deletion is fragile, and the always-loaded file carried fields most projects don't have. | A small generic starter (`generic/`), with the competition and data parts as optional `profiles/`. The embedded template is the third profile. |
| 5 | `/start` had no agreed stop condition, and `/wrap` rewrote several files every session. | The inner loop is where tokens go; it needs an objective end. Wrap overhead matters when sessions are short. | The plan must name **done when:** a command. `/wrap` only touches files with something new and lists the files changed. |
| 6 | The guide said pi accepts a Claude Pro/Max subscription login. | Your notes say it doesn't run on the plan, and that is right in effect: Anthropic bills third-party harnesses separately. | GUIDE §B3 corrected; SHORT-LOOP §4 explains which agent for which billing. |
| 7 | The kit called you a beginner. | Your own notes say embedded systems engineer. | Corrected in the instructions the agents read (`/define`, the kit's AGENTS.md, the planning-chat text). |

Full argument for items 3–5: `workflow/WORKFLOW.md` §9. Item 4 was revised in pass 5.

## Pass 3 (November 2026): bugs reproduced and fixed, switch to pi

The kit was checked again against your notes, this time by running it: the tool
tests, the host tests, the project generator, and the serial tool against a
simulated board. Four bugs showed up, and the harness changed.

| # | Finding | Why it matters | Change |
|---|---|---|---|
| 1 | `make loop PORT=/dev/ttyACM1` flashed that port, but boot-check, the on-board tests and the bench tests talked to whichever board was auto-detected. | With both boards plugged in you flash one and test the other, and the result looks green. | `PORT=` and the new `BOARD=R\|C` are passed to every step, including pytest. Covered by a test. |
| 2 | `T-TOUCH` could not fail. Touch detection falls back to "resistive" whenever no GT911 answers, and the test only failed for "none", which never happens. | A C board whose GT911 isn't detected looked exactly like a healthy R board. "Works on both boards" passed from one board's run. | Each board is registered once by its USB serial number (`esp_serial.py register R`). The self test is told which controller that board must have and fails on a mismatch. REQ-003 is now `T-TOUCH@R, T-TOUCH@C` and needs a run on each board. An unregistered board only passes on a positively detected GT911. |
| 3 | The "done" gate accepted stale results: break the code after a test run and `make trace RUN=1` still printed `TRACE:OK`. | That gate is what `/build-loop` relies on before ticking a plan item. | Every result is stamped with a fingerprint of its source. The firmware carries its own (`build=` in `info` and `selftest`), so a target or bench result is tied to what is really on the board. A mismatch shows as `STALE` and fails the gate. |
| 4 | `new-embedded-project` failed halfway when git had no name/email yet, left the folder behind, then refused to re-run. | A first-time user hits this on step one. | It checks before creating anything and says what to run. |
| 5 | The harness was Claude Code. You use **pi**. | Skills, the permission allowlist and the setup script didn't apply. | The slash commands are now pi prompt templates in `prompts/` (same names: `/define`, `/commission`, …). `CLAUDE.md` became `AGENTS.md`. The setup script installs pi. The Claude Code allowlist is gone, because pi never asks before running a command. |
| 6 | The guide said the worst case was "re-clone the project". | pi runs everything unprompted, the agent's account may manage the network (which includes reading saved Wi-Fi passwords), and a normal `gh` login reaches every repo you own. | GUIDE §6 rewritten around this. New steps: forget the home Wi-Fi on the dev box, use a GitHub token limited to chosen repos. `setup-root.sh` warns about saved Wi-Fi networks. The polkit rule itself is unchanged (narrowing it can't be tested without the T480s). |
| 7 | The install steps pointed at an empty default branch. | "Download ZIP" and `gh repo clone` fetched a blank README. | The kit is merged to `master`, and the guide uses the folder name GitHub's ZIP really has. |
| 8 | Smaller things | | New `make open-check` (see below). `device.wait_for()` for bench tests that wait for a state change. Commissioning no longer needs Ethernet for the template's own bench tests. `make ci-fw` no longer claims to need no toolchain. |

## Pass 2 (November 2026): traceability and sturdier checks

- `tools/trace.py` / `make trace`: FSD requirement → named test → last result.
- `T-BOOT` added (the FSD cited it but it didn't exist); baseline REQ-001…006.
- Serial tool: more crash signatures (S3 watchdog resets, task watchdog, asserts,
  stack overflows); boot-check keeps watching after `BOOT:OK`; a FAIL line can't
  be outvoted by the `DONE` count.
- GT911 reset-sequence fallback before assuming the resistive board.
- `make ci-fw`: flash the binaries GitHub CI built.
- `bench-wifi` hotspot no longer auto-starts after a reboot.

## Pass 1 (November 2026): the first version

Guide, template project, setup scripts, bench scripts and the workflow commands,
mapped from the three videos onto your two laptops and two boards.

## What still needs your hands

Nothing here has run on real hardware. In the order you will meet them:

1. **Debian on the T480s.** `setup-root.sh` has never run on Debian (it was
   checked with `bash -n` and stub commands only). Step 6 must report the Wi-Fi
   card as managed by NetworkManager. After the reboot, close the lid with
   nobody logged in: SSH from the Legion must still answer. `bluetoothctl show`
   must list a controller.
2. **Claude Code, the allowlist and the slash commands.** After `setup-user.sh`,
   start `claude` in a project and type `/` : `/start`, `/wrap`, `/define` and
   the others should be offered. Then `make check` must run without a permission
   prompt, and so must the first `/wrap`'s `tail -n 15` of `docs/history.md`. If
   not, see troubleshooting.
3. **The serial tool against a real board.** Everything in the loop goes through
   it. `/commission` exercises it step by step; the first one may need fixes.
4. **`make open-check`.** On the ESP32-S3's built-in USB the DTR/RTS lines double
   as reset signals, and Linux toggles them when a port is opened. If that resets
   your board, the check says so (`OPENCHECK:RESETS`). Single commands still
   work then, but multi-step bench tests would lose device state between steps.
5. **R board**: `make loop BOARD=R`. If `T-BOOT` fails, look at `boot_ms=`. The 2 s
   USB wait in `setup()` counts toward it, so a value just under 3000 is plausible.
6. **C board**: `make loop BOARD=C`. `T-TOUCH` now fails if the GT911 isn't found.
   If the serial log says "GT911 answered after reset", the fallback was needed;
   record that in the board file.
7. **The resistive controller itself** can't be detected electrically. The
   corner-tap step in `/commission` is its only proof.
8. On the T480s: `bench-wifi up` / `down` and `bench-mqtt start` once by hand
   before trusting bench tests.

## Not changed, on purpose

- **No Wi-Fi/MQTT code in the template.** The first project that needs it writes
  it through `/define` → `/start`, with bench tests. The fixtures
  (`wifi_ap`, `mqtt_broker`, `device.wait_for`) are in place.
- **No ESP-IDF switch yet.** Arduino + arduino-cli is the right level for now.
- **The polkit rule is still broad** (all NetworkManager actions for `embdev`).
  The mitigation is procedural: no saved home Wi-Fi on the dev box.
- **`bench-mqtt` listens on all interfaces without a password.** It is a
  throw-away test broker, but anything on your home network can reach it while
  it runs. Stop it when you're done (`bench-mqtt stop`).
