# The Embed_WF guide: an AI-assisted ESP32 workflow on hobby hardware

This guide turns the ideas from the three videos in your notes into a setup that
runs on **what you already own**: the Legion laptop, the ThinkPad T480s, your two
Guition JC4827W543 boards and a Claude Pro subscription. Nothing to buy except
maybe an Ethernet cable.

Read it top to bottom once. After that, use the [cheat sheet](cheatsheet.md).

---

## 0. The big picture in one minute

The videos describe a shift: **you stop writing code and start writing
specifications and tests**. An AI agent writes the code, compiles it, flashes it,
reads the serial output, and fixes its own mistakes. It keeps going until the
tests you agreed on pass. You stay the boss: you decide *what* gets built and
whether it's *done*.

To make that safe and practical you need four things:

| Need | Video's answer | Your answer |
|---|---|---|
| An agent that can edit a whole project and run commands | Claude Code | Claude Code (included in Claude Pro) |
| A box where the agent may do anything without wrecking your real PC | Proxmox VM / container | **The T480s**, under a separate Linux user `embdev` |
| Hands and eyes on the real board | Raspberry Pi "workbench" | **The T480s again**: USB to the board, its Wi-Fi as a test hotspot, MQTT broker, Bluetooth |
| A safety net and history | GitHub | GitHub (+ free CI that compiles every push) |

```
 ┌──────────────────────────┐   SSH / VS Code    ┌────────────────────────────────┐   USB-C   ┌──────────────┐
 │ Legion (Windows 10)      │ ─────────────────▶ │ T480s (Linux Mint) "dev box"   │ ────────▶ │ Guition R/C  │
 │ - Claude Desktop: ideas, │                    │ - user embdev (no sudo)        │           │ ESP32-S3     │
 │   chat, spec reviews     │                    │ - Claude Code + arduino-cli    │ ◀─ Wi-Fi ─│ board        │
 │ - VS Code: view files    │                    │ - bench-wifi (test hotspot)    │  (test    └──────────────┘
 │ - your personal stuff    │                    │ - bench-mqtt, bench-ble-scan   │  network)
 └──────────────────────────┘                    └───────────────┬────────────────┘
                                                                 │ Ethernet → router → internet
                                                                 ▼
                                                     GitHub (repo + CI compile)
```

**Why not run the agent on the Windows laptop directly?** You can, but the videos'
advice is sound: an agent you let run freely should live on a machine where a
mistake costs nothing. The Legion holds your personal life. And its Windows 10
is out of security updates: the free EU extended-update year ran out in
October 2026. (Side note: the Legion's i5-9300H is on Microsoft's Windows 11
CPU list, so a free upgrade to Windows 11 is probably open to you. Check with
Microsoft's *PC Health Check* app. That's worth doing for your own safety,
whatever you decide about this workflow.) The T480s is a spare. Linux is also simply
the smoother environment for `make`, serial ports, hotspots and the tooling here.

**Why not buy a Raspberry Pi like the video?** You don't need one yet. Video 3
uses the Pi because its dev machine is a VM with no free USB or Wi-Fi. Your T480s
has real USB ports, real Wi-Fi and Bluetooth, and an Ethernet port, so it can be
the dev box *and* the test bench. Its 8 GB of RAM and 4-core i5 are plenty for
arduino-cli and Claude Code. Claude itself runs in the cloud.

---

## 1. The ten levels: where you are, and where this repo takes you

| Level (video 1) | Meaning | In this setup |
|---|---|---|
| 0 Vibe coding | copy/paste from a chat | What you've probably done in Claude Desktop. Still fine for quick questions. |
| 1 Spec-driven | describe, don't code | `docs/IDEA.md` |
| 2 FSD documents | spec as a Markdown file | `docs/FSD.md`, generated with `/define` |
| 3 Agents | Claude Code edits the project folder | Claude Code on the dev box |
| 4 GitHub | history + protection | every project is a repo; CI compiles each push |
| 5 Execution control | agent runs commands itself | permission allowlist in `.claude/settings.json` |
| 6 Dev VM | isolate the agent | `embdev` user on the T480s |
| 7 Parallel projects + memory | one folder per project, `CLAUDE.md` memory | `~/projects/<name>/`, each with its own `CLAUDE.md`, `PLAN.md`, `NOTES.md` |
| 8 CLI build/flash/monitor | agent sees compiler + serial output | `make loop`, `tools/esp_serial.py` |
| 9 Datasheets | agent reads PDFs | `datasheets/` + `/datasheet` |
| 10 Beyond Arduino | ESP-IDF | later, see §9 |

Video 3 adds the **harness**, the closed loop
*spec → test → code → build → flash → test → fix*. In this repo that's the
skills `/define` → `/commission` → `/build-loop`, driven by the `make` targets and
the four test tiers (host → target → bench → field). See [testing.md](testing.md).

---

## 2. What's in this repo

```
Embed_WF/
├── docs/
│   ├── GUIDE.md            ← you are here
│   ├── cheatsheet.md       daily commands and prompts
│   ├── testing.md          the four test tiers explained
│   └── troubleshooting.md
├── hardware/
│   ├── machines.md         your laptops and their roles
│   └── boards/guition-jc4827w543.md   board reference (your file); copied into every project
├── devbox/
│   ├── setup-root.sh       part 1: packages, embdev user, permissions (run with sudo)
│   └── setup-user.sh       part 2: arduino-cli, ESP32 core, Claude Code, skills, bench tools
├── bench/                  bench-wifi, bench-mqtt, bench-ble-scan (the "test lab")
├── skills/                 Claude Code skills: /new-project /define /commission
│                           /build-loop /datasheet /change-request /wrap-up
├── tools/new_project.sh    creates ~/projects/<name> from the template
├── tests/                  tests for the template's Python tools (run by CI)
└── template/               a complete, working starter project (see below)
```

The **template** is a real firmware for your board, not an empty shell. It starts
the display, auto-detects R vs C touch, draws your touches, and has a serial
console (`help`, `info`, `selftest`, `text …`, `bl …`). It also has 14 host
tests, 7 on-board tests and a pytest bench suite. Its FSD already lists the
requirements those tests prove, so `make trace` shows how traceability works. Every new project starts from
it, so the plumbing is proven before you add features.

---

## 3. Part A — prepare the Windows laptop (≈ 30 min)

1. **GitHub account.** If you don't have one, create it at github.com. This repo
   lives there already.
2. **VS Code.** Install it from code.visualstudio.com, then install the extensions
   **Remote - SSH** (Microsoft) and **Claude Code** (Anthropic). This gives you
   the project file tree the video author missed. You'll browse and edit files
   that live on the T480s as if they were local. A Samba share works too, but
   Remote-SSH is simpler and needs nothing on the Linux side except SSH.
3. **SSH client.** It's built into Windows 10. Open *Windows Terminal* or
   *PowerShell* and run `ssh -V` to check.
4. **Markdown viewer.** VS Code's preview (`Ctrl+Shift+V`) is free and enough.
   Typora (as in video 1) or Obsidian are nicer for long specs. That's optional.
5. **Claude Desktop stays useful.** Make a *Project* called "ESP32 boards" and
   upload `hardware/boards/guition-jc4827w543.md`. Paste the text from
   [claude-desktop-project.md](claude-desktop-project.md) into the project's
   instructions. Use it for thinking out loud, drafting `IDEA.md`, explaining
   concepts, or reviewing an FSD you paste in. Chat is level 0–2; Claude Code on
   the dev box is level 3+.
6. **Optional: drive the dev box from Claude Desktop itself.** Recent versions of
   Claude Desktop have a **Code** tab that can run Claude Code on another machine
   over SSH. In the Code tab's environment selector, look for an option to add an
   SSH connection, and enter `embdev@<t480s-ip>` (set up the SSH key from §B5
   first). Desktop installs Claude Code on the T480s by itself. The agent then
   runs **on the T480s** as `embdev`, exactly as in a terminal, so the safety
   model doesn't change. You get it in the app you already use. Two caveats: the
   feature is new and its menus move between versions, and its built-in terminal
   panel may be unavailable for SSH sessions. Keep a plain `ssh` window open for
   `make`, `tmux` and the like. If your version doesn't have it, the terminal or
   VS Code route below works the same way.

> Arduino IDE on Windows still works for quick experiments. The board file's
> Tools settings are unchanged. Just don't flash the same board from both
> machines at once.

---

## 4. Part B — turn the T480s into the dev box (≈ 1–2 h, mostly downloads)

### B1. Before you start

- **Back up the file dump.** You're about to give an AI agent an account on this
  machine. Step B2 locks your files away from it, but a backup is cheap
  insurance. Copy anything important to an external drive or the Legion.
- **Update Mint.** Use the Update Manager, apply everything, and reboot. Then
  check *System Info*: Mint 21.x or 22.x are both fine.
- **Ethernet.** Plug the T480s into your router with a cable. The test hotspot
  (`bench-wifi`) takes over the Wi-Fi card, so internet must come over the cable.
  `bench-wifi` refuses to start if the cable isn't there, so you can't cut
  yourself off by accident. A cheap USB Wi-Fi dongle also works.
- **Lid and power.** Go to *Power Management*, set "When the lid is closed" to
  **Do nothing** (on AC power), and disable suspend on AC. The laptop can then
  sit closed on a shelf like a little server. Keep it plugged in.
- **Give it a fixed address.** In your router, reserve a DHCP address for the
  T480s (for example 192.168.1.50). `t480s.local` often works from Windows too,
  but an IP always works.

### B2. System setup (from your normal Mint account)

Download this repo as a ZIP from GitHub (green **Code** button → *Download ZIP*),
extract it to `~/Downloads/Embed_WF`, open a terminal and run:

```bash
sudo bash ~/Downloads/Embed_WF/devbox/setup-root.sh embdev
```

It asks for a password for the new `embdev` user. Then it:

- creates `embdev` **without** admin rights, and makes the other home folders
  private (so the agent can't read your file dump)
- installs git, make, g++, Python + pyserial + pytest, pdftotext, Mosquitto,
  NetworkManager tools, BlueZ, tmux, SSH server and GitHub CLI
- removes `brltty`, a braille daemon that steals USB-serial ports on Ubuntu-based systems
- puts `embdev` in the `dialout` group (serial port access)
- lets `embdev` start or stop the Wi-Fi hotspot without sudo (a polkit rule)

Read the script first if you like. It's commented line by line. It's safe to run twice.

### B3. User setup (as embdev)

Log out, then log in as **embdev**, or from Windows run `ssh embdev@<t480s-ip>`.
Then:

```bash
gh auth login
```

```bash
gh repo clone adilary/embed_wf ~/Embed_WF
```

```bash
bash ~/Embed_WF/devbox/setup-user.sh
```

This installs arduino-cli, the ESP32 core (≈ 1 GB, pinned to 3.3.10) and Arduino_GFX
(1.6.8). It also installs Claude Code, links the skills into
`~/.claude/skills`, and installs the `bench-*` commands and
`new-embedded-project`.

Open a **new** terminal and log in to Claude:

```bash
claude
```

Choose "Claude account" and sign in with your Pro subscription. Type `/exit` when done.

Set your git identity once:

```bash
git config --global user.name "Your Name"
```

```bash
git config --global user.email "you@example.com"
```

### B4. Smoke test with a board

Plug the **R** board into the T480s with a USB-C **data** cable, then:

```bash
arduino-cli board list
```

You should see something like `/dev/ttyACM0 … ESP32 Family Device`. If not, see
[troubleshooting](troubleshooting.md).

### B5. Connect comfortably from Windows

- **SSH key** (so you never type the password). In PowerShell on the Legion:
  ```powershell
  ssh-keygen -t ed25519
  ```
  ```powershell
  type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh embdev@<t480s-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
  ```
- **VS Code.** Press `F1` → *Remote-SSH: Connect to Host…* → `embdev@<t480s-ip>` →
  *Open Folder* → `~/projects/<name>`. Open a terminal in VS Code (`` Ctrl+` ``)
  and run `claude`. Or use the Claude Code panel. Either way it runs **on the
  T480s**.
- **Long runs: use tmux.** `tmux new -s work` then `claude`. If Wi-Fi drops or you
  close the laptop, reconnect and `tmux attach -t work`, and the agent is still
  going. That's how you "go for lunch" like in the video.
- **Checking in from your phone while out on a job (optional).** Claude Code's
  *Remote Control* lets the Claude mobile app or claude.ai follow and steer a
  session that keeps running **on the T480s**. Inside a running session type
  `/remote-control` (or start one with `claude remote-control`), then open the
  link or QR code on your phone. Run it inside `tmux` so the session survives
  your SSH window closing. If the T480s sleeps or `claude` exits, the remote view
  ends too. It's tied to a Claude subscription (Pro works per Anthropic's
  announcement). The exact command names have changed between versions, so if
  these don't work, check `claude --help` or the Claude Code docs.

---

## 5. Part C — your first project, end to end

Do this once with the template's own demo before building anything real. It
proves every link in the chain.

```bash
new-embedded-project hello-board
```

```bash
cd ~/projects/hello-board && claude
```

Inside Claude Code, in this order:

1. **`/commission`**. Claude checks the toolchain, runs host tests, compiles,
   flashes the board, verifies boot and runs the on-board self test. Then it
   asks you to swap to the **C** board and repeats. The capacitive (GT911) code
   has never run on your board, so this is where it gets verified or fixed.
   Finally it asks you to tap the screen corners to calibrate the resistive
   touch.
2. Push it to GitHub. Tell Claude "create a private GitHub repo for this and push".
   Watch the **Actions** tab on github.com: CI compiles the firmware there too.

When that's green, your whole pipeline works. Now a real project:

```bash
new-embedded-project desk-clock
```

1. Write `docs/IDEA.md` in your own words. For example:
   > A desk clock that shows time and date in big digits, gets the time from the
   > internet, shows the indoor temperature from a sensor I'll attach, and dims
   > the screen at night. Touching the screen switches to a page with min/max
   > temperature today. Must work on both my boards.
2. `claude` → **`/define`**. It asks one question at a time with suggested
   answers, then writes `docs/FSD.md`. Every requirement gets an ID and a test
   tier. Then it writes `docs/PLAN.md`, split into phases. **Read the FSD
   carefully.** This is the one document that matters; edit it until it says
   what you want.
3. If you add a part (a sensor), drop its PDF into `datasheets/` and run
   **`/datasheet bme280.pdf`**.
4. **`/commission`** (quick this time).
5. **`/build-loop`**. Claude implements phase 1: tests first, then code, then
   host test → compile → flash → boot check → target test → fix → repeat. It
   stops and asks when it needs your hands (wiring, swapping boards) or when a
   decision isn't covered by the FSD.
6. Check the result on the real device yourself. That's the human's half of the
   job.
7. **`/wrap-up`** updates the docs, commits and pushes.
8. Next session: `claude` in the folder → `/build-loop` again. `CLAUDE.md`,
   `PLAN.md` and `NOTES.md` give it back its memory. You can also use
   `claude --continue` to resume the last conversation.

Want something changed later? **`/change-request` the clock should also show the
weekday**. The spec gets updated first, then the code.

---

## 6. Permissions and safety: how much freedom to give the agent

Claude Code asks before running commands. You choose how often:

| Setting | What happens | Use it |
|---|---|---|
| Default + this repo's allowlist | `make`, `arduino-cli`, the serial tool, `git commit`, bench commands run without asking. Everything else asks. `sudo` is blocked. | **Start here.** The template's `.claude/settings.json` sets this up. |
| Accept-edits mode (`Shift+Tab` to cycle modes) | file edits don't ask either | once you trust the flow |
| `claude --dangerously-skip-permissions` (the video's "superclaude") | nothing asks | **only** as `embdev` on the T480s, only inside a project folder, never on the Legion |

Why `embdev` makes the last row acceptable: it can't `sudo`, can't read your
files, and everything it touches is in git and on GitHub. The worst case is
"re-clone the project" or, at very worst, "re-run the setup scripts".

**Be clear about what the allowlist is.** It saves you from clicking "yes" 200
times. It is **not** a security wall. `make` runs whatever the Makefile says, and
`pytest` runs whatever Python the agent puts in `test/bench/`, and the agent can
edit both. The things that actually protect you are: the agent runs as `embdev`
(no sudo, your files locked away), the project is in git, and secrets never go on
that machine except throw-away bench credentials. That's also why the template's
`secrets.h` holds only the `embtest` hotspot password, never your home Wi-Fi.

If you want the video's shortcut, add this to embdev's `~/.bashrc`:

```bash
alias superclaude='claude --dangerously-skip-permissions'
```

Other rules baked into the template's `CLAUDE.md`:

- Secrets go in `firmware/src/secrets.h`, which is git-ignored and which Claude
  is blocked from reading.
- Tests never touch your home Wi-Fi or your real Home Assistant MQTT. They use
  `bench-wifi` and `bench-mqtt`.
- `git push` happens only when you ask, or in `/wrap-up`.

---

## 7. Making the most of Claude Pro

Pro includes Claude Code, but usage is metered in rolling windows. Coding agents
read a lot, so you can hit the limit in a long session. To stretch it:

- **One task per conversation.** Use `/clear` when switching topics. Use
  `/compact` when a long session gets slow.
- **Let the files be the memory**, not the chat. That's what `PLAN.md` and
  `NOTES.md` are for. A fresh session with good files beats a bloated old one.
- **Fast tiers first.** Host tests cost almost nothing. Flashing and long serial
  captures cost more tokens (the output is read). The template is built around
  this.
- **Summaries before datasheets.** `/datasheet` once, then the agent reads the
  150-line summary instead of a 90-page PDF.
- **Plan in Claude Desktop, build in Claude Code.** Brainstorming in chat doesn't
  eat into a build session.
- `/model` lets you pick the model. A lighter model is often enough for routine
  loops; switch up for hard debugging.
- `/usage` (or `/status`, depending on version) shows where you stand.
- If you regularly run out, the Max plan exists. Upgrade only once the workflow
  is clearly paying off.

---

## 8. Testing: the part you can't hand over

The agent writes code. **You** decide what "working" means. That happens in the
FSD's requirements table: every requirement says how it will be proven, and at
which tier. The full explanation is in [testing.md](testing.md). In short:

| Tier | Runs on | Speed | Example for your board |
|---|---|---|---|
| host | the T480s CPU, `g++` | < 1 s | word wrapping, parsing, clock maths, sensor conversion formulas |
| target | the ESP32 | ~1–2 min (compile + flash) | PSRAM present, NVS save/load, display init, touch detected |
| bench | ESP32 + T480s Wi-Fi/MQTT/BLE | minutes | joins `embtest` hotspot, reconnects when `bench-wifi down/up`, publishes to `bench-mqtt` |
| field / manual | the real world, you | — | "readable from across the room", "touch feels right" |

Video 3's key insight applies fully: **negative tests** (Wi-Fi gone, broker down,
garbage input) are where automation pays off. You would never test those by hand
after every change, and now you don't have to.

**`make trace` ties it together.** It reads the FSD's requirements table, checks
that every test named there exists, and shows the last result of each:

```
| REQ-010 | host   | PASS    | mbus_decode_e450, mbus_crc_bad   | Decodes E450 frames ... |
| REQ-020 | target | NOT RUN | no result yet: T-NVS             | Stores credentials ...  |
| REQ-030 | bench  | NO TEST | no bench test named test_req_030_*| Reconnects after ...   |
```

`NO TEST` means "specified but not proven", the to-do list. `/build-loop`
won't tick a plan item until `make trace RUN=1 REQS="…"` says `TRACE:OK`, and
`/wrap-up` saves the table as `docs/STATUS.md`. That table is your answer to "is
it done?". Read it and the FSD; you don't need to read the code.

---

## 9. Where to go next (when the basics feel boring)

- **Verify the C (GT911) touch code** during your first `/commission`, and copy
  what you learn back into `hardware/boards/guition-jc4827w543.md`. That file
  is the shared memory across all your projects.
- **A second board type?** Add `hardware/boards/<board>.md` in the same style and
  a second FQBN to a project's Makefile.
- **Level 10, ESP-IDF.** When a project needs features Arduino hides (fine
  power management, advanced BLE, OTA with rollback), start a project with
  "use ESP-IDF instead of Arduino" in the FSD. The agent can restructure the
  template (`idf.py build flash`, Unity tests) and update the Makefile targets.
  `esp_serial.py` and the bench tools work unchanged. ESP-IDF's toolchain is
  big (≈ 3 GB). Video 3's trick of compiling it only in GitHub CI is worth it
  then.
- **Dedicated bench hardware.** If the T480s ever needs its Wi-Fi back, a
  Raspberry Pi (as in video 3) or a second ESP32 acting as a stimulus generator
  (fake sensors, MBus or Modbus simulators) becomes useful. The bench scripts
  are the interface, so tests won't need rewriting.
- **Parallel projects.** Each project is a folder and repo. Run one `claude` per
  tmux window. One board per project at a time, or pass `PORT=/dev/ttyACM1` to
  `make`.
- **A VM on the Legion** is possible (16 GB RAM), but USB passthrough for
  flashing is fiddly on Windows. The T480s is the better dev box.
- **Let GitHub compile (video 3's trick).** Once a project is on GitHub, every
  push builds the firmware in CI. `make ci-fw` downloads the binaries CI built
  for the current commit, and `make upload` flashes them, with no local compile.
  It's handy when the T480s is busy or for an ESP-IDF project whose toolchain
  you'd rather not install. For the everyday Arduino loop a local
  `make compile` is faster, because it doesn't wait for the push and the CI queue.

---

## 10. Glossary

- **Agent**: an AI that can act (edit files, run commands), not only chat.
- **Claude Code**: Anthropic's coding agent; runs in a terminal or VS Code.
- **CLAUDE.md**: a file Claude Code reads automatically at the start of every session in that folder. It's the project's standing instructions.
- **Skill**: a reusable instruction pack, invoked as `/name`. Ours live in `skills/`.
- **FSD**: Functional Specification Document. What the product must do, as testable requirements.
- **FQBN**: Fully Qualified Board Name, arduino-cli's string for "board + all Tools menu settings".
- **CI**: Continuous Integration. GitHub compiles and tests every push on its own servers.
- **Host / target**: host = the PC doing the building; target = the ESP32 running the result.
- **Closed loop**: the agent sees the results of its own changes (compiler output, serial log, tests) and reacts, without you copy-pasting in between.
