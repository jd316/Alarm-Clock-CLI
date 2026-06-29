# Alarm Clock CLI — Plan

> Pre-build thinking for a Python CLI alarm clock. Written before code, on purpose:
> the exercise grades *how I make and defend engineering decisions*, not feature count.

## 1. Problem definition

Build an **interactive CLI alarm clock** in Python. Constraints given: CLI only — no web
UI, no React, no database. No detailed spec; scope is mine to set in the time available.

The judging rubric is the real spec: *problem definition, design decisions, directing AI,
reviewing output, validating the result*. So the target is a **small, correct, well-reasoned
program**, not a feature pile. Over-building loses points here.

### The one decision that drives everything
No database + "interactive CLI" ⇒ a long-running session. So **alarms live in memory for the
life of the process**. "Survives restart" is therefore *out of scope by design*, not by
neglect — and I'll say so out loud.

## 2. Scope

**In:**
- Set an alarm — absolute `HH:MM` (24h) and relative `+10m` / `+30s` / `+2h`
- List alarms
- Cancel an alarm
- Snooze (classic 9 min)
- Rings while you keep using the prompt (background watcher)

**Out — named, with the trigger to add it:**
| Cut | Add when |
|---|---|
| Disk persistence | alarms must survive restart → JSON file, still no DB |
| Recurring / daily alarms | a real wake-routine is needed |
| Custom sound files / timezones | the environment demands it |
| Non-interactive `argparse` mode | something needs to script it |

## 3. Design — stdlib only, one file `alarm.py`

| Concern | Choice | Why |
|---|---|---|
| Interactive shell | `cmd.Cmd` (stdlib) | free REPL + `do_*` dispatch + `help`, vs a hand-rolled `input()` loop |
| Background ringing | one daemon `threading.Thread`, 1s tick | keep typing while alarms fire |
| Shared alarm list | `list` + one `threading.Lock` | `# ponytail: global lock, fine for a handful of alarms` |
| Sound | terminal bell `\a` + printed banner | zero-dep; **knob**: env var / `sound` cmd to run a custom player, since audio is environment-specific |
| Time parse | `datetime.strptime` for `HH:MM`, small regex for `+Nm/Ns/Nh` | stdlib |

**Trickiest logic** (the part worth a test): *next occurrence*. `07:30` when it's already
`08:00` must roll to tomorrow. Relative offsets are just `now + delta`.

```
alarm.py
  parse_when(s, now) -> datetime      # absolute rolls to tomorrow if already past; relative = now+delta
  AlarmClock(cmd.Cmd)
    do_set / do_list / do_cancel / do_snooze / do_quit
    _watcher()                        # daemon: every 1s, ring + drop any due alarm
  __main__: asserts on parse_when, then app.cmdloop()
```

## 4. Build order (~30 min)

1. `parse_when` + asserts (5m) — get today/tomorrow rollover right first.
2. `cmd.Cmd` shell: `set` / `list` / `cancel` (10m).
3. Watcher thread + ring + `snooze` (10m).
4. README + a `+5s` demo run on camera (5m).

## 5. Validation

- **Automated:** running `python alarm.py` fires `assert` self-checks on `parse_when`
  (past time rolls forward, relative math) before launching the shell — the one runnable
  check the logic gets.
- **Manual / on camera:** `set +5s`, keep typing `list`, watch it ring → `snooze` → `cancel`.

## 6. README + narration

README covers: what it does, how to run, and **the scope decisions and why** (in-memory by
design, bell over an audio lib, `cmd.Cmd` over a loop) plus the named cut list. On camera I
narrate the *decisions*, not the typing: refining the spec down, the one tricky function and
its test, and what I deliberately left out.
