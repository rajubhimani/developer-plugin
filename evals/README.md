# Evals

Each folder is one case for `claude plugin eval`: a realistic prompt in `prompt.md` and a grader
in `graders/` that checks the right skill was loaded. They guard skill **triggering**: if a
description change makes a skill stop firing, a case here fails.

Run them with `make evals` (about $6 and three minutes on your own Claude account, so they are
opt-in and not part of `make check`). `make check` does run a free static check that every case
is well formed and names a skill that exists.

**Triggering is probabilistic.** So `make evals` runs each case three times and passes a case at two
of three. A single failure is noise; a case that keeps failing is a real regression. With the current
descriptions all 16 cases passed 48 of 48 runs. Before they were shortened, `accessibility` and
`concurrency` loaded in none of three runs.

Descriptions share one list with every other installed skill, and Claude Code cuts them when it is
full, so `make check` caps their total length. Re-run before and after any change to a description.
Whether skills improve answers is measured separately in `../quality/`.

Each run uses your own Claude allowance (the whole suite is 48 sessions). If you hit your usage limit
the remaining cases report `exit 1` and a limit message: that is not a failing skill, so re-run later.
