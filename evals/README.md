# Evals

Each folder is one case for `claude plugin eval`: a realistic prompt in `prompt.md` and a grader
in `graders/` that checks the right skill was loaded. They guard skill **triggering**: if a
description change makes a skill stop firing, a case here fails.

Run them with `make evals` (about $3 and two minutes on your own Claude account, so they are
opt-in and not part of `make check`). `make check` does run a free static check that every case
is well formed and names a skill that exists.

**Triggering is probabilistic.** Across 41 runs, 40 loaded the right skill; the one miss was
`secrets-and-config`, where the model answered without loading the skill. So `make evals` runs
each case three times and passes a case at two of three. A single failure is noise; a case that
keeps failing is a real regression.

Descriptions were not rewritten to say only "Use when ...", as another plugin recommends: our
skills were loaded in 40 of 41 runs, so the change would add regression risk for little gain.
Re-run before and after any change to a description.

Each run uses your own Claude allowance (the whole suite is 24 sessions). If you hit your usage limit
the remaining cases report `exit 1` and a limit message: that is not a failing skill, so re-run later.
