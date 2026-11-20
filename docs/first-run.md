# First run: from a bare T480s to a commissioned board

Everything needed to set up the dev box and take the first project through
commissioning, in order, on one page. About 2–3 hours, mostly downloads.
Nothing has run on real hardware yet, so each step says what you should see.
Note what differs; that is the most useful thing this run produces.

**You need:** the T480s on Linux Mint 21.x or 22.x, an Ethernet cable to your
router, both Guition boards (R and C) with USB-C **data** cables, the Legion for
SSH, a GitHub account, and a Claude plan (Pro or Max).

---

## 1. Prepare the T480s (your normal Mint account)

- **Back up** anything you care about on it.
- **Update Mint:** Update Manager, apply everything, reboot.
- **Ethernet:** plug it into the router. The test hotspot takes over the Wi-Fi
  card later, so internet must come over the cable.
- **Forget your home Wi-Fi** once the cable works (*Network Connections* → select
  it → delete). The agent's account may manage the network, which would let it
  read saved Wi-Fi passwords.
- **Lid and power:** *Power Management* → lid closed on AC: **Do nothing**;
  disable suspend on AC. Keep it plugged in.
- **Fixed address:** reserve a DHCP address for it in your router (e.g.
  `192.168.1.50`). Below, `<t480s-ip>` means that address.

## 2. System setup (once, with sudo)

Download Embed_WF as a ZIP from GitHub (**Code** → *Download ZIP*); the folder is
`Embed_WF-master`. Then:

```bash
sudo bash ~/Downloads/Embed_WF-master/devbox/setup-root.sh embdev
```

It asks for a password for the new `embdev` user, then runs 8 steps: the user
(no sudo), private home folders, packages, GitHub CLI, serial ports (`dialout`,
removes `brltty`), hotspot permission, Mosquitto, firewall.

**Expect:** it ends without an error. If it lists saved Wi-Fi networks, delete
them (`sudo nmcli connection delete "<name>"`).

## 3. As embdev: identity, GitHub, the kit

From the Legion (PowerShell):

```powershell
ssh embdev@<t480s-ip>
```

Git identity (the project generator refuses to run without it):

```bash
git config --global user.name "Your Name"
```

```bash
git config --global user.email "you@example.com"
```

GitHub: on github.com create a **fine-grained token** (*Settings → Developer
settings → Personal access tokens → Fine-grained*) limited to `Embed_WF` and the
project repos you'll make, with Contents and Workflows read/write, Actions and
Metadata read. Then paste it when asked (*GitHub.com → HTTPS → Paste a token*,
yes to "authenticate Git"):

```bash
gh auth login
```

```bash
gh repo clone adilary/embed_wf ~/Embed_WF
```

## 4. The short-loop workflow (once)

The session commands (`/start`, `/wrap`, `/judge`) live in their own repository.
Set its address once, here; it moves to GitLab later:

```bash
WF_URL=https://github.com/AdilAry/Workflow
```

```bash
git clone "$WF_URL" ~/Workflow
```

```bash
bash ~/Workflow/install.sh
```

**Expect:** `Saved WORKFLOW_DIR=/home/embdev/Workflow in ~/.bashrc`, then
"No agent harness found". That's right: Claude Code comes in the next step.

Open a **new** terminal (or `exit` and SSH in again), then check:

```bash
echo $WORKFLOW_DIR
```

**Expect:** `/home/embdev/Workflow`.

## 5. Toolchain, agent and commands (once)

```bash
bash ~/Embed_WF/devbox/setup-user.sh
```

Seven steps: PATH, arduino-cli, ESP32 core + Arduino_GFX (≈ 1 GB), Claude Code,
the slash commands, bench commands, checks.

**Expect:** step 5 lists `/judge /start /wrap /change-request /commission
/datasheet /define /new-project`; step 7 says `dialout: ok` (if not: log out and
in again) and `gh: logged in`.

Open a **new** terminal, then log Claude Code in to your Claude plan:

```bash
claude
```

Over SSH it prints a link: open it on the Legion, log in, paste the code back.
`/exit` to leave.

Fill the one bracket in your "How I work" file (the areas you're new to):

```bash
nano ~/.claude/CLAUDE.md
```

## 6. Smoke test with a board

Plug in the **R** board:

```bash
arduino-cli board list
```

**Expect:** a line like `/dev/ttyACM0 … ESP32 Family Device`. Nothing? Try
another cable (many are charge-only) or port, and check `id` shows `dialout`.

## 7. The first project

```bash
new-embedded-project hello-board
```

```bash
cd ~/projects/hello-board && claude
```

**The two checks this whole setup stands on:**

1. Type `/` : `/start`, `/wrap`, `/commission`, `/define` and the others must be
   offered.
2. Ask it to run `make check`. It must run **without** a permission prompt
   (`.claude/settings.json` allows it). If it asks, note it: the allowlist needs
   fixing.

Optional, for CI: the narrow token can't create repos, so create an empty
`hello-board` repo on github.com, add it to the token's repository list, then:

```bash
git remote add origin https://github.com/<you>/hello-board.git && git push -u origin main
```

## 8. Commissioning: `/commission`

In Claude Code, in the project, type `/commission`. The agent works through
Phase 0 of `docs/PLAN.md` and reports each step as ✅ or ❌. Your part:

| When it asks | You |
|---|---|
| Which board is plugged in? | **R** = resistive (soft plastic screen), **C** = capacitive (glass). It registers each board once. |
| Upload can't connect | Hold BOOT, tap RESET, release BOOT. |
| `OPENCHECK:RESETS` | Opening the port restarts the board. Note it; multi-step bench tests can't be trusted until fixed. |
| Plug in the other board | Plug in the C board; both may stay plugged in from now on. |
| Tap the four corners | Tap them while it watches the serial output. This is the only proof the resistive touch works. |
| Push to GitHub? | Yes if you did the optional step in §7. |

**Expect at the end:** `make trace RUN=1` prints `TRACE:OK`, with REQ-001…006
`PASS` (REQ-003 needs a run on **both** boards). The C board's touch code is the
least proven part: if `T-TOUCH` fails on C, the agent fixes it in this session.

Then type `/wrap`. It commits, says which files changed and what to check, and
leaves the next step in `PROGRESS.md`. Then `/clear`.

## 9. After commissioning: the normal loop

1. Write your idea in plain words in `docs/IDEA.md` (5–15 sentences).
2. `/define`: it asks one question at a time, then writes `docs/FSD.md` (the
   spec, every requirement with an ID and a test) and `docs/PLAN.md`. Read the
   FSD carefully; edit it until it says what you want. `/wrap`, `/clear`.
3. From then on, one plan item per session:
   - `/start` (or `/start REQ-010`): it replies with at most five bullets and a
     **done when** line. Correct it or say OK. Nothing changes before your OK.
   - It works on its own until the tests pass, or stops to ask you.
   - `/wrap`, then check what it tells you to check on the real board, then `/clear`.
4. Every few items: `/judge` in a **fresh** session.

Habits: one task per session; at about 40% context (`/context`) finish the step
and `/wrap`; on a wrong path, `Esc Esc` to rewind instead of correcting; `Esc`
stops the agent at once.

## 10. Comfort from the Legion

- **SSH key** (PowerShell, once):
  ```powershell
  ssh-keygen -t ed25519
  ```
  ```powershell
  type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh embdev@<t480s-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
  ```
- **VS Code:** extension *Remote - SSH* → `F1` → *Connect to Host* →
  `embdev@<t480s-ip>` → open `~/projects/hello-board`.
- **tmux** for long runs: `tmux new -s work`, then `claude`. After a dropped
  connection: `tmux attach -t work`. `claude -c` resumes the last session.

## 11. When something goes wrong

| Symptom | Fix |
|---|---|
| `setup-user.sh` says the workflow was not found | `echo $WORKFLOW_DIR` is empty: run `bash ~/Workflow/install.sh`, open a new terminal, run it again. |
| `claude: command not found` | Open a new terminal. Otherwise re-run `setup-user.sh`. |
| `/start` etc. not offered | `ls ~/.claude/commands` must list them. If not: `bash ~/Embed_WF/tools/install-workflow.sh`, then a new session. Still nothing: add `--copy`. |
| Every `make` asks for approval | Started outside the project folder, or `.claude/settings.json` is missing. |
| Board not found / port vanishes | Data cable, another port, `id` shows `dialout`. `brltty` must be gone (`setup-root.sh` removes it). |
| Upload fails | Hold BOOT, tap RESET, release BOOT, then `make upload`. |
| `new-embedded-project` refuses: git identity | Run the two `git config --global` lines in §3. |
| `gh repo create` refused | Expected with the narrow token: create the repo on github.com (§7). |
| SSH times out | The T480s is asleep: check lid and suspend settings (§1). |

## 12. Bring back

After the run, note these, so the next session can fix what didn't work:

1. Were the commands offered, and did `make check` run without a prompt (§7)?
2. Did the serial tool work end to end (`/commission` steps 4–8)?
3. `make open-check`: `OPENCHECK:OK` or `RESETS`?
4. R board: did `T-BOOT` pass? What was `boot_ms=`?
5. C board: did `T-TOUCH` pass? Did the log say "GT911 answered after reset"?
6. Did the corner taps land near the corners?
7. Optional: `bench-wifi up` / `down` and `bench-mqtt start` / `stop` by hand.

Anything true for the board itself (a pin quirk, a proven init sequence) goes
into `~/Embed_WF/hardware/boards/guition-jc4827w543.md`.
