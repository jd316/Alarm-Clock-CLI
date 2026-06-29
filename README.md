# Alarm Clock CLI

An interactive command-line alarm clock in Python. **Stdlib only** — no dependencies,
no database, no web UI. Alarms live in memory for the life of the session (see *Decisions*).

## Run

```bash
python3 alarm.py        # then type `help`
```

Running it first executes built-in self-checks on the time parser, then starts the shell.

## Commands

| Command | What it does |
|---|---|
| `set 07:30 wake up` | alarm at 07:30 (rolls to tomorrow if already past), label "wake up" |
| `set +5s tea` | alarm 5 seconds from now (`+Ns` / `+Nm` / `+Nh`) |
| `list` | show pending alarms |
| `cancel 1` | cancel alarm #1 |
| `snooze [min]` | re-arm the last alarm that rang (default 9 min) |
| `quit` | exit |

It rings with the terminal bell while you keep typing. For real audio, point
`ALARM_SOUND` at a player command:

```bash
ALARM_SOUND="aplay /usr/share/sounds/alarm.wav" python3 alarm.py
```

## Decisions (the interesting part)

- **In-memory, not persisted.** "No database" + "interactive CLI" means a long-running
  session, so alarms live in memory. Survival across restarts is *out of scope by design*,
  not by neglect. Add it (a JSON file) when a real need appears.
- **`cmd.Cmd` for the shell.** Stdlib gives the REPL, command dispatch, and `help` for free
  — less code than a hand-rolled `input()` loop.
- **One daemon thread + a lock.** A background thread ticks every second and fires due
  alarms while the main thread reads your input. One global lock guards the list — fine for
  a handful of alarms.
- **Terminal bell over an audio library.** Zero-dependency and works everywhere; `ALARM_SOUND`
  is the calibration knob for environments that want real sound.

See [PLAN.md](PLAN.md) for the full pre-build reasoning, scope, and what was deliberately cut.

## What's deliberately out

Recurring/daily alarms, disk persistence, timezones, and a non-interactive `argparse` mode —
each listed in [PLAN.md](PLAN.md) with the trigger that would justify adding it.

## Validation

- **Automated:** `parse_when` self-checks (past-time rollover, relative offsets, bad input)
  run on every startup.
- **Manual:** `set +5s tea`, keep typing `list`, watch it ring, then `snooze` / `cancel`.
