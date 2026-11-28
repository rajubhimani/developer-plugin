# Quality evals

Do the skills improve answers, not just load? Each case is run with and without the plugin and a
judge model checks four points, one grader per point. `Δ` is what the plugin added.

Run with `make quality-evals`. It uses your own Claude allowance (more than `make evals`, because
every case runs twice and a judge grades each answer), so it is opt-in.

**Read it with care.** The first two runs graded all four points in one rubric. The judge failed
answers that held all four, and the same setup run twice moved one case from 0 to 1.00. Over both
runs (six runs per case and arm) the average score was 0.72 with the plugin and 0.58 without. Only
`column-rename` (6 of 6 against 0 of 6) and `leaked-key` (6 of 6 against 2 of 6) showed a clear
gain; the other differences are within the noise. The one-grader-per-point layout has not been run
yet. Use several runs per case before believing a change, and do not edit a skill only to satisfy
a judge.
