# The Embed_WF guide: an AI-assisted ESP32 workflow on hobby hardware

This guide turns the ideas from the three videos in your notes into a setup that
runs on **what you already own**: the Legion laptop, the ThinkPad T480s, your two
Guition JC4827W543 boards and the **pi** coding agent with whichever model
provider you use. Nothing to buy except maybe an Ethernet cable.

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
| An agent that can edit a whole project and run commands | Claude Code | **pi** (pi.dev), your harness of choice |
| A box where the agent may do anything without wrecking your real PC | Proxmox VM / container | **The T480s**, under a separate Linux user `embdev` |
| Hands and eyes on the real board | Raspberry Pi "workbench" | **The T480s again**: USB to the boards, its Wi-Fi as a test hotspot, MQTT broker, Bluetooth |
| A safety net and history | GitHub | GitHub (+ free CI that compiles every push) |

```
 ┌──────────────────────────┐   SSH / VS Code    ┌────────────────────────────────┐   USB-C   ┌──────────────┐
 │ Legion (Windows)         │ ─────────────────▶ │ T480s (Linux Mint) "dev box"   │ ────────▶ │ Guition R+C  │
 │ - chat app: ideas, spec  │                    │ - user embdev (no sudo)        │           │ ESP32-S3     │
 │   reviews                │                    │ - pi agent + arduino-cli       │ ◀─ Wi-Fi ─│ boards       │
 │ - VS Code: view files    │                    │ - bench-wifi (test hotspot)    │  (test    └──────────────┘
 │ - your personal stuff    │                    │ - bench-mqtt, bench-ble-scan   │  network)
 └──────────────────────────┘                    └───────────────┬────────────────┘
                                                                 │ Ethernet → router → internet
                                                                 ▼
                                                     GitHub (repo + CI compile)
```

**Why not run the agent on the Windows laptop directly?** You can, but the videos'
advice is sound: an agent you let run freely should live on a machine where a
mistake costs nothing. That matters even more with pi, which **never asks before
running a command** (see §6). The Legion holds your personal life. If it still
runs Windows 10, it is also out of security updates: the free EU extended-update
year ran out in October 2026. (Side note: the Legion's i5-9300H is on Microsoft's
Windows 11 CPU list, so a free upgrade is probably open to you. Check with
Microsoft's *PC Health Check* app.) The T480s is a spare. Linux is also simply
the smoother environment for `make`, serial ports, hotspots and the tooling here.

**Why not buy a Raspberry Pi like the video?** You don't need one yet. Video 3
uses the Pi because its dev machine is a VM with no free USB or Wi-Fi. Your T480s
has real USB ports, real Wi-Fi and Bluetooth, and an Ethernet port, so it can be
the dev box *and* the test bench. Its 8 GB of RAM and 4-core i5 are plenty for
arduino-cli and pi. The model itself runs in the cloud.

---

## 1. The ten levels: where you are, and where this repo takes you

| Level (video 1) | Meaning | In this setup |
|---|---|---|
| 0 Vibe coding | copy/paste from a chat | What you've probably done in a chat app. Still fine for quick questions. |
| 1 Spec-driven | describe, don't code | `docs/IDEA.md` |
| 2 FSD documents | spec as a Markdown file | `docs/FSD.md`, generated with `/define` |
| 3 Agents | an agent edits the project folder | pi on the dev box |
| 4 GitHub | history + protection | every project is a repo; CI compiles each push |
| 5 Execution control | agent runs commands itself | pi does this by default, with no permission prompts |
| 6 Dev VM | isolate the agent | `embdev` user on the T480s |
| 7 Parallel projects + memory | one folder per project, an instructions file as memory | `~/projects/<name>/`, each with its own `AGENTS.md`, `PROGRESS.md`, `docs/history.md` |
| 8 CLI build/flash/monitor | agent sees compiler + serial output | `make loop`, `tools/esp_serial.py` |
| 9 Datasheets | agent reads PDFs | `datasheets/` + `/datasheet` |
| 10 Beyond Arduino | ESP-IDF | later, see §9 |

Video 3 adds the **harness**, the closed loop
*spec → test → code → build → flash → test → fix*. In this repo that loop runs
*inside* one short session: `/define` and `/commission` once, then
`/start <one plan item>` … `/wrap`, again and again. It is driven by the `make`
targets and the four test tiers (host → target → bench → field). See
[testing.md](testing.md).

**Where this differs from the video on purpose.** The video lets the agent run a
whole phase and comes back after lunch. Here the unit is one plan item per
session, with two gates that are yours: you approve a five-bullet plan before any
file changes, and you check the result before the next item starts. The agent
still iterates on its own between the gates, against the tests. That costs
fewer tokens (every session starts small and ends before the context rots) and
keeps you in the loop by design. The method is the short-loop workflow in
[workflow/WORKFLOW.md](../workflow/WORKFLOW.md); the embedded parts are built on top of it.

A word on the word: video 3's "harness" is the whole coupling of agent, method and
test bench. **pi** is an *agent harness*, the program that lets a model edit files
and run commands. This repo supplies the rest: the method (`prompts/`), the
project skeleton (`template/`) and the bench (`bench/`).

---

## 2. What's in this repo

```
Embed_WF/
├── docs/
│   ├── GUIDE.md            ← you are here
│   ├── cheatsheet.md       daily commands and prompts
│   ├── testing.md          the four test tiers explained
│   ├── troubleshooting.md
│   ├── planning-chat.md    using a chat app for the thinking part
│   └── REVIEW.md           what has been reviewed, changed and not yet verified
├── hardware/
│   ├── machines.md         your laptops and their roles
│   └── boards/guition-jc4827w543.md   board reference (your file); copied into every project
├── devbox/
│   ├── setup-root.sh       part 1: packages, embdev user, permissions (run with sudo)
│   └── setup-user.sh       part 2: arduino-cli, ESP32 core, pi, short-loop workflow, bench tools
├── bench/                  bench-wifi, bench-mqtt, bench-ble-scan (the "test lab")
├── workflow/               the short-loop workflow for ANY software project: guide,
│                           /start /wrap /judge, "How I work" file, generic project starter.
│                           Also shipped on its own as a zip (tools/build-workflow-zip.sh)
├── prompts/                the embedded slash commands: /define /commission /datasheet
│                           /change-request /new-project
├── tools/                  new_project.sh (creates ~/projects/<name>), install-workflow.sh,
│                           build-workflow-zip.sh
├── tests/                  tests for the template's Python tools (run by CI)
└── template/               a complete, working starter project (see below)
```

The **template** is a real firmware for your board, not an empty shell. It starts
the display, auto-detects R vs C touch, draws your touches, and has a serial
console (`help`, `info`, `selftest`, `text …`, `bl …`). It also has 14 host
tests, 7 on-board tests and a pytest bench suite. Its FSD already lists the
requirements those tests prove, so `make trace` shows how traceability works.
Every new project starts from it, so the plumbing is proven before you add
features. Nothing in the template depends on pi: it is `make` and Python, so it
would work the same under another agent.

---

## 3. Part A — prepare the Windows laptop (≈ 30 min)

1. **GitHub account.** If you don't have one, create it at github.com. This repo
   lives there already.
2. **VS Code.** Install it from code.visualstudio.com, then install the extension
   **Remote - SSH** (Microsoft). This gives you the project file tree the video
   author missed. You'll browse and edit files that live on the T480s as if they
   were local. A Samba share works too, but Remote-SSH is simpler and needs
   nothing on the Linux side except SSH.
3. **SSH client.** It's built into Windows. Open *Windows Terminal* or
   *PowerShell* and run `ssh -V` to check.
4. **Markdown viewer.** VS Code's preview (`Ctrl+Shift+V`) is free and enough.
   Typora (as in video 1) or Obsidian are nicer for long specs. That's optional.
5. **A chat app stays useful** for thinking out loud, drafting `IDEA.md`,
   explaining concepts, or reviewing an FSD you paste in. See
   [planning-chat.md](planning-chat.md) for a ready-made setup. Chat is level
   0–2; pi on the dev box is level 3+.

> Arduino IDE on Windows still works for quick experiments. The board file's
> Tools settings are unchanged. Just don't flash the same board from both
> machines at once. A build made in the IDE reports `build=unknown`, so
> `make trace` won't count tests run against it (see §8).

---

## 4. Part B — turn the T480s into the dev box (≈ 1–2 h, mostly downloads)

### B1. Before you start

- **Back up anything you care about on it.** You're about to give an AI agent an
  account on this machine. Step B2 locks your files away from it, but a backup is
  cheap insurance. Copy anything important to an external drive or the Legion.
- **Update Mint.** Use the Update Manager, apply everything, and reboot. Then
  check *System Info*: Mint 21.x or 22.x are both fine.
- **Ethernet.** Plug the T480s into your router with a cable. The test hotspot
  (`bench-wifi`) takes over the Wi-Fi card, so internet must come over the cable.
  `bench-wifi` refuses to start if the cable isn't there, so you can't cut
  yourself off by accident. A cheap USB Wi-Fi dongle also works.
- **Forget your home Wi-Fi on this machine.** Once the cable works, remove the
  saved home network (*Network Connections* → select it → delete). The agent's
  account is allowed to manage the network so it can run the test hotspot, and
  that permission would also let it read saved Wi-Fi passwords. `setup-root.sh`
  lists any that are still saved.
- **Lid and power.** Go to *Power Management*, set "When the lid is closed" to
  **Do nothing** (on AC power), and disable suspend on AC. The laptop can then
  sit closed on a shelf like a little server. Keep it plugged in.
- **Give it a fixed address.** In your router, reserve a DHCP address for the
  T480s (for example 192.168.1.50). `t480s.local` often works from Windows too,
  but an IP always works.

### B2. System setup (from your normal Mint account)

Download this repo as a ZIP from GitHub (green **Code** button → *Download ZIP*).
GitHub names the extracted folder after the branch, `Embed_WF-master`. Open a
terminal and run:

```bash
sudo bash ~/Downloads/Embed_WF-master/devbox/setup-root.sh embdev
```

It asks for a password for the new `embdev` user. Then it:

- creates `embdev` **without** admin rights, and makes the other home folders
  private (so the agent can't read your files)
- installs git, make, g++, Python + pyserial + pytest, pdftotext, Mosquitto,
  NetworkManager tools, BlueZ, tmux, SSH server and GitHub CLI
- removes `brltty`, a braille daemon that steals USB-serial ports on Ubuntu-based systems
- puts `embdev` in the `dialout` group (serial port access)
- lets `embdev` start or stop the Wi-Fi hotspot without sudo (a polkit rule), and
  warns you about saved Wi-Fi networks

Read the script first if you like. It's commented line by line. It's safe to run twice.

### B3. User setup (as embdev)

Log out, then log in as **embdev**, or from Windows run `ssh embdev@<t480s-ip>`.

Set your git identity first (the project generator needs it):

```bash
git config --global user.name "Your Name"
```

```bash
git config --global user.email "you@example.com"
```

Then connect GitHub. **Give this machine a token that only reaches the repos the
agent should touch**, not your whole account: on github.com go to *Settings →
Developer settings → Personal access tokens → Fine-grained tokens*, create one
limited to this repo and your project repos (Contents and Workflows: read and
write; Actions and Metadata: read), and paste it when `gh` asks:

```bash
gh auth login
```

(Choose *GitHub.com* → *HTTPS* → *Paste an authentication token*, and say yes
to "authenticate Git".) The price of the narrow token: it can't create
repositories. For each new project, make an empty repo on github.com yourself
and add it to the token's repository list; the agent does the rest. The quick
browser login avoids that chore, but it hands the agent's account the keys to
every repository you own. Your call; §6 explains the stakes.

```bash
gh repo clone adilary/embed_wf ~/Embed_WF
```

```bash
bash ~/Embed_WF/devbox/setup-user.sh
```

This installs arduino-cli, the ESP32 core (≈ 1 GB, pinned to 3.3.10) and Arduino_GFX
(1.6.8). It also installs **pi** and the short-loop workflow: the slash commands
are linked into `~/.pi/agent/prompts/` (that is what makes `/start`, `/wrap`, `/define` and
friends exist; linked, so a later `git pull` in `~/Embed_WF` updates them by itself) and your
"How I work" file is copied to `~/.pi/agent/AGENTS.md`. Open that
file once and fill its one bracket. Last, it installs the `bench-*` commands,
`new-embedded-project` and `new-project`.

Open a **new** terminal and connect pi to a model:

```bash
pi
```

Type `/login`, pick your provider and follow the prompts: an OpenAI (ChatGPT)
login, GitHub Copilot, or an API key from most providers. Then `/model` to choose
the model, and `/quit` when done.

**About Claude and pi.** A Claude Pro/Max plan's usage limits do not cover pi.
Anthropic bills third-party harnesses separately (extra usage or API rates; the
terms changed several times during 2026, so check the current ones before you
count on it). If you want Claude models on your subscription, use Claude Code.
The projects don't care: each has an `AGENTS.md` for pi and a one-line
`CLAUDE.md` that makes Claude Code read the same file, and
`tools/install-workflow.sh` installs the same slash commands for both. See
[WORKFLOW.md](../workflow/WORKFLOW.md) §6. If you do run Claude Code on the dev box, run
it as `embdev` too.

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
  and run `pi`. It runs **on the T480s**.
- **Long runs: use tmux.** `tmux new -s work` then `pi`. If Wi-Fi drops or you
  close the laptop, reconnect and `tmux attach -t work`, and the agent is still
  going. That's how you "go for lunch" like in the video. The same trick works
  from a phone with any SSH app.

---

## 5. Part C — your first project, end to end

Do this once with the template's own demo before building anything real. It
proves every link in the chain.

```bash
new-embedded-project hello-board
```

```bash
cd ~/projects/hello-board && pi
```

Inside pi, in this order:

1. **`/commission`**. The agent checks the toolchain, runs host tests, compiles,
   asks you which board is plugged in and **registers** it (R or C, once per
   board), flashes it, verifies boot, checks that opening the serial port doesn't
   reset the board, and runs the on-board self test. Then it asks for the **C**
   board and repeats. Both boards can stay plugged in from then on. The
   capacitive (GT911) code has never run on your board, so this is where it gets
   verified or fixed. Finally it asks you to tap the screen corners to calibrate
   the resistive touch.
2. Push it to GitHub. Create an empty private repo `hello-board` on github.com,
   add it to the dev box's token (§B3), then tell the agent "push this to my
   GitHub repo hello-board". Watch the **Actions** tab on github.com: CI compiles
   the firmware there too.

When that's green, your whole pipeline works. Now a real project:

```bash
new-embedded-project desk-clock
```

1. Write `docs/IDEA.md` in your own words. For example:
   > A desk clock that shows time and date in big digits, gets the time from the
   > internet, shows the indoor temperature from a sensor I'll attach, and dims
   > the screen at night. Touching the screen switches to a page with min/max
   > temperature today. Must work on both my boards.
2. `pi` → **`/define`**. It asks one question at a time with suggested
   answers, then writes `docs/FSD.md`. Every requirement gets an ID and a test
   tier. Then it writes `docs/PLAN.md`, split into phases. **Read the FSD
   carefully.** This is the one document that matters; edit it until it says
   what you want.
3. If you add a part (a sensor), drop its PDF into `datasheets/` and run
   **`/datasheet bme280.pdf`**.
4. **`/commission`** (quick this time: the boards are already registered).

Each of the steps above is its own session: end it with **`/wrap`**, then
`/new`. From here on, every session has the same shape:

5. **`/start`** (it takes "Next" from `PROGRESS.md`; or name the item:
   `/start REQ-010`). The agent reads that plan item and its FSD rows and replies
   with at most five bullets: steps, files, and **done when:**
   `make trace RUN=1 REQS="REQ-010"`. Correct it or say OK. Nothing has changed
   yet.
6. The agent works that one item: tests first, then code, then host test →
   compile → flash → boot check → target test → fix → repeat, until the trace
   gate is green. It stops and asks when it needs your hands (wiring, a board
   that isn't plugged in), when it would have to leave the plan, when a decision
   isn't covered by the FSD, when the same failure has survived three different
   fixes, or after ten flash-and-test runs without a pass (the Run limit). A bare
   board on USB is flashed without asking. If the FSD says the board drives
   something that can move, heat, switch mains or charge a battery, the plan says
   so and the agent flashes only after your OK for that session.
7. **`/wrap`**. It runs the checks, rewrites `PROGRESS.md`, refreshes
   `docs/STATUS.md`, commits and pushes, and tells you what to look at.
   **Finished means checked by you.** An item with a `field` or `manual`
   requirement, or one that changes the screen, is not ticked yet: it sits under
   "Waiting on me" as "awaiting my check". Look at the real device. That's the
   human's half of the job.
8. `/new` (or quit and start `pi` again), then **`/start`** for the next item.
   The fresh session knows where it is from `PROGRESS.md` alone. It first asks
   whether the item awaiting your check passed, and only then ticks it and
   writes its history entry. One you reject becomes that session's task.

Every few items, and before you call the project done, run **`/judge`** in a
fresh session: it reviews the firmware against the FSD without having built it,
and ranks what it finds by value per hour of fixing.

Want something changed later? **`/change-request` the clock should also show the
weekday**. The spec and plan get updated in that session; the code is the next
`/start`.

---

## 6. Safety: pi never asks, so the account is the wall

Some agents ask before each command and let you build an allowlist. **pi does
not.** In its own words: "No permission popups. Run in a container." It shows
you every file read, command and edit, but it doesn't wait for a yes. That is
video 1's "superclaude"/YOLO mode, permanently on.

So the protection is not in the agent. It is in where the agent runs:

| What protects you | How |
|---|---|
| `embdev` has no `sudo` | the agent can't change the system or install system packages |
| other home folders are private | it can't read your files on the T480s |
| every project is in git and on GitHub | a wrecked folder is one `git clone` away |
| a fine-grained GitHub token (§B3) | the agent can push only to the repos you listed, not delete your account's other work |
| no real secrets on the machine | `secrets.h` holds only the throw-away `embtest` hotspot password; your home Wi-Fi isn't saved (§B1) |

Be honest about the worst case. With all of the above in place it is "re-clone
the project" or, at very worst, "re-run the setup scripts". **Skip the token step
or leave the home Wi-Fi saved, and the worst case grows** to "every GitHub repo
you own" and "your Wi-Fi password". An agent also reads things you didn't write
(datasheets, web pages, library code), and text in those can try to steer it.
That is why the limits live in the account, not in asking the agent nicely.

Rules of thumb:

- Run `pi` **only** as `embdev` on the T480s, and only inside a project folder.
  Never on the Legion.
- Watch the first sessions. `Esc` stops the agent at once.
- The rules the agent is asked to follow are in the template's `AGENTS.md`:
  credentials only in the git-ignored `firmware/src/secrets.h`; tests never touch
  your home Wi-Fi or your real Home Assistant MQTT (they use `bench-wifi` and
  `bench-mqtt`); `git push` only in `/wrap` or when you ask; never edit the
  result files under `build/`. Those are instructions, not locks.

---

## 7. Keeping usage down

Whether you pay per token or have a subscription with a quota, coding agents read
a lot. To stretch it:

- **One task per session.** That is the whole method: `/start`, work, `/wrap`,
  `/new`. A long session re-reads everything it has already said on every turn.
  `/compact` only rescues a session you can't end yet.
- **Let the files be the memory**, not the chat. That's what `PROGRESS.md` (a
  snapshot under 60 lines, rewritten every `/wrap`) and `docs/history.md` (read
  only when asked)
  are for. A fresh session with good files beats a bloated old one.
- **Fast tiers first.** Host tests cost almost nothing. Flashing and long serial
  captures cost more tokens (the output is read). The template is built around
  this.
- **Summaries before datasheets.** `/datasheet` once, then the agent reads the
  150-line summary instead of a 90-page PDF.
- **Plan in a chat app, build in pi.** Brainstorming in chat doesn't eat into a
  build session.
- `/model` (or `Ctrl+L`) switches the model. A lighter model is often enough for
  routine loops; switch up for hard debugging.
- `/session` shows the tokens and cost of the current session; the footer shows
  them all the time.

---

## 8. Testing: the part you can't hand over

The agent writes code. **You** decide what "working" means. That happens in the
FSD's requirements table: every requirement says how it will be proven, and at
which tier. The full explanation is in [testing.md](testing.md). In short:

| Tier | Runs on | Speed | Example for your board |
|---|---|---|---|
| host | the T480s CPU, `g++` | < 1 s | word wrapping, parsing, clock maths, sensor conversion formulas |
| target | the ESP32 | ~1–2 min (compile + flash) | PSRAM present, NVS save/load, display init, right touch controller found |
| bench | ESP32 + T480s Wi-Fi/MQTT/BLE | minutes | joins `embtest` hotspot, reconnects when `bench-wifi down/up`, publishes to `bench-mqtt` |
| field / manual | the real world, you | — | "readable from across the room", "touch feels right" |

Video 3's key insight applies fully: **negative tests** (Wi-Fi gone, broker down,
garbage input) are where automation pays off. You would never test those by hand
after every change, and now you don't have to.

**`make trace` ties it together.** It reads the FSD's requirements table, checks
that every test named there exists, and shows the last result of each:

```
| REQ-010 | host   | PASS    | mbus_decode_e450, mbus_crc_bad     | Decodes E450 frames ... |
| REQ-015 | host   | STALE   | logic or host tests changed since… | Rejects bad CRC ...     |
| REQ-020 | target | NOT RUN | no result yet: T-NVS               | Stores credentials ...  |
| REQ-030 | bench  | NO TEST | no bench test named test_req_030_* | Reconnects after ...    |
```

`NO TEST` means "specified but not proven", the to-do list. `STALE` means the
test passed, **but on older code**: every result carries a fingerprint of the
source it ran against, and the firmware reports the fingerprint it was built
from, so a pass can't outlive the code it tested. It is the **Done gate**: `/wrap` won't tick a plan
item until `make trace RUN=1 REQS="…"` says `TRACE:OK`, and it saves the
table as `docs/STATUS.md`. That table is your answer to "is it done?". Read it
and the FSD; you don't need to read the code.

**Two boards.** Each board is registered once as R or C (`/commission` does it).
After that `make loop BOARD=C` flashes *and* tests the C board, even with both
plugged in, and the self test knows which touch controller that board must have.
A requirement that must hold on both lists its test twice, `T-TOUCH@R, T-TOUCH@C`,
and only turns PASS after a run on each.

---

## 9. Where to go next (when the basics feel boring)

- **Verify the C (GT911) touch code** during your first `/commission`, and copy
  what you learn back into `hardware/boards/guition-jc4827w543.md`. That file
  is the shared memory across all your projects.
- **Use the second board as a test instrument.** A laptop has no GPIO, but you
  own two boards with free pins (headers P2–P5). Wire a few pins of one to the
  other and the second board can press "buttons", feed UART data or fake a
  sensor for the first. Bench tests drive both with `BOARD=R` / `BOARD=C`.
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
  Raspberry Pi (as in video 3) becomes useful. The bench scripts are the
  interface, so tests won't need rewriting.
- **Parallel projects.** Each project is a folder and repo. Run one `pi` per
  tmux window, and give each project its own board with `BOARD=R` / `BOARD=C`.
- **A VM on the Legion** is possible (16 GB RAM), but USB passthrough for
  flashing is fiddly on Windows. The T480s is the better dev box.
- **Let GitHub compile (video 3's trick).** Once a project is on GitHub, every
  push builds the firmware in CI. `make ci-fw` downloads the binaries CI built
  for the current commit, and `make upload` flashes them, with no local compile.
  Flashing still uses arduino-cli and the installed ESP32 core, so this saves
  compile time, not the install. For the everyday Arduino loop a local
  `make compile` is faster, because it doesn't wait for the push and the CI queue.

---

## 10. Glossary

- **Agent**: an AI that can act (edit files, run commands), not only chat.
- **Agent harness**: the program around the model that gives it those hands. Here: **pi**.
- **pi**: an open-source terminal coding agent (pi.dev). Works with many model providers. Never asks before running a command.
- **AGENTS.md**: a file pi reads automatically at the start of every session in that folder. It's the project's standing instructions.
- **Slash command / prompt template**: a reusable instruction file, invoked as `/name`. Ours live in `workflow/templates/commands/` and `prompts/`; `tools/install-workflow.sh` links them into pi (`~/.pi/agent/prompts/`) and Claude Code (`~/.claude/commands/`).
- **Short loop**: one task per session, with files (`PROGRESS.md` first) carrying the memory to the next one. See workflow/WORKFLOW.md.
- **Done gate**: the command a task must pass before it counts as finished. Here: `make trace RUN=1 REQS="…"`.
- **FSD**: Functional Specification Document. What the product must do, as testable requirements.
- **FQBN**: Fully Qualified Board Name, arduino-cli's string for "board + all Tools menu settings".
- **CI**: Continuous Integration. GitHub compiles and tests every push on its own servers.
- **Host / target**: host = the PC doing the building; target = the ESP32 running the result.
- **Closed loop**: the agent sees the results of its own changes (compiler output, serial log, tests) and reacts, without you copy-pasting in between.
- **Build id**: a fingerprint of the firmware source, baked into the firmware by `make compile`. It lets `make trace` tell whether a test result belongs to the current code.
