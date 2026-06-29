#!/usr/bin/env python3
"""Interactive CLI alarm clock. Stdlib only. Alarms live in memory for the session.

Usage:  python alarm.py        # then type `help`
See PLAN.md for the why behind every choice.
"""
import cmd
import os
import re
import threading
import time
from datetime import datetime, timedelta

_REL = re.compile(r"^\+(\d+)([smh])$")
_UNIT = {"s": "seconds", "m": "minutes", "h": "hours"}


def parse_when(s, now):
    """'HH:MM' (rolls to tomorrow if already past) or '+Ns/+Nm/+Nh' (now + delta)."""
    s = s.strip()
    m = _REL.match(s)
    if m:
        return now + timedelta(**{_UNIT[m.group(2)]: int(m.group(1))})
    t = datetime.strptime(s, "%H:%M").time()          # raises ValueError on junk
    when = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    return when if when > now else when + timedelta(days=1)


def ring(label):
    # ponytail: terminal bell; set ALARM_SOUND to a shell command for real audio.
    print(f"\n\a*** ALARM: {label} ({datetime.now():%H:%M:%S}) ***")
    cmd_ = os.environ.get("ALARM_SOUND")
    if cmd_:
        os.system(cmd_)  # ponytail: ALARM_SOUND is the user's own env var, meant to be a shell command — shell is the feature, not a sink


class AlarmClock(cmd.Cmd):
    intro = "Alarm clock. `set 07:30 wake up` or `set +5s tea`. Type `help`."
    prompt = "alarm> "

    def __init__(self):
        super().__init__()
        self.alarms = []            # list of [id, fire_at, label]
        self.next_id = 1
        self.last_label = None      # for snooze
        self.lock = threading.Lock()  # ponytail: one global lock, fine for a handful of alarms
        threading.Thread(target=self._watch, daemon=True).start()

    def _watch(self):
        while True:
            time.sleep(1)
            now = datetime.now()
            with self.lock:
                due = [a for a in self.alarms if a[1] <= now]
                self.alarms = [a for a in self.alarms if a[1] > now]
            for _id, _at, label in due:
                self.last_label = label
                ring(label)
            if due:
                print(self.prompt, end="", flush=True)

    def _add(self, fire_at, label):
        with self.lock:
            aid = self.next_id
            self.next_id += 1
            self.alarms.append([aid, fire_at, label])
        print(f"#{aid} set for {fire_at:%Y-%m-%d %H:%M:%S} — {label}")

    def do_set(self, arg):
        """set <HH:MM | +Ns/+Nm/+Nh> [label] — schedule an alarm."""
        parts = arg.split(maxsplit=1)
        if not parts:
            print("usage: set <HH:MM | +Ns/+Nm/+Nh> [label]")
            return
        try:
            fire_at = parse_when(parts[0], datetime.now())
        except ValueError:
            print(f"bad time '{parts[0]}'. use HH:MM or +Ns/+Nm/+Nh")
            return
        self._add(fire_at, parts[1] if len(parts) > 1 else "alarm")

    def do_list(self, arg):
        """list — show pending alarms."""
        with self.lock:
            alarms = sorted(self.alarms, key=lambda a: a[1])
        if not alarms:
            print("no alarms set.")
        for aid, at, label in alarms:
            print(f"#{aid}  {at:%Y-%m-%d %H:%M:%S}  {label}")

    def do_cancel(self, arg):
        """cancel <id> — remove an alarm."""
        if not arg.strip().isdigit():
            print("usage: cancel <id>")
            return
        aid = int(arg)
        with self.lock:
            before = len(self.alarms)
            self.alarms = [a for a in self.alarms if a[0] != aid]
            gone = before - len(self.alarms)
        print(f"cancelled #{aid}" if gone else f"no alarm #{aid}")

    def do_snooze(self, arg):
        """snooze [minutes] — re-arm the last alarm that rang (default 9 min)."""
        if self.last_label is None:
            print("nothing to snooze.")
            return
        mins = int(arg) if arg.strip().isdigit() else 9
        self._add(datetime.now() + timedelta(minutes=mins), self.last_label)

    def do_quit(self, arg):
        """quit — exit."""
        return True

    do_EOF = do_quit


def _selfcheck():
    base = datetime(2026, 6, 29, 8, 0, 0)
    assert parse_when("09:00", base) == base.replace(hour=9, minute=0)          # later today
    assert parse_when("07:30", base) == base.replace(hour=7, minute=30) + timedelta(days=1)  # rolled
    assert parse_when("+5s", base) == base + timedelta(seconds=5)
    assert parse_when("+2h", base) == base + timedelta(hours=2)
    try:
        parse_when("nope", base); assert False
    except ValueError:
        pass


if __name__ == "__main__":
    _selfcheck()
    try:
        AlarmClock().cmdloop()
    except KeyboardInterrupt:
        print()
