# EXER048 — Release-Gated Evaluation

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec048.html](../Lecture/lectures/lec048.html)

## Goal

Make the capstone evaluation a gate that every change passes before it ships: compare each release
with an approved baseline per category, fail on a regression, and run it on every pull request without
secrets.

## The project

| File | Status | Your work |
|---|---|---|
| `release_gate.py` | TODO | `prompt_version`, `compare`, `gate` |
| `release-gate.yml` | TODO | the GitHub Actions workflow: a replay job and a live job |
| `baseline.json` | given | the approved per-category results, with the release they were measured on |
| `recordings.json` | given | the capstone's recorded replies to every evaluation question |

Given: `current_release` (prompt version, tools version, model), the `Recorder` and `Replayer`, and the
`record`, `approve` and `gate` commands. Scoring is the EXER037 reference code, unchanged.

| Mode | Runs | Needs | Catches |
|---|---|---|---|
| `gate --replay` | the recorded replies through the capstone's scoring | nothing | changes to cases and scoring; a prompt or tool change without new recordings |
| `gate --live` | the real evaluation | `.env` / secrets | changes in what the model answers |

## Run it

```bash
uv run python EXER048/starter/release_gate.py gate --replay      # offline, deterministic
uv run python EXER048/starter/release_gate.py gate --live        # live: about 2 minutes
uv run python EXER048/check.py
```

After a change that passes, `release_gate.py record` (live) and `release_gate.py approve --by <name>` make it the
new baseline; commit `baseline.json` and `recordings.json` with the change.

## Success criteria

- [ ] A prompt gets the same version id until its text changes; line endings do not matter
- [ ] Safety fails on any drop; other categories fail beyond the tolerance or below the capstone's bar; a dropped category fails, a new one warns
- [ ] The report shows both releases, marks what changed, has a row per category, and says how to approve a passing change
- [ ] Replay reproduces the baseline from the recordings, and refuses recordings made for another prompt
- [ ] The workflow replays on pull requests without secrets, runs live by hand with secrets, and uploads the report even when the gate fails
- [ ] All 8 checks pass (offline)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Take one prompt change through the gate: the baseline's memory category is 3/4 because the assistant refuses to use the conversation itself. *Done when:* replay refuses the changed prompt, the live gate passes with memory improved, and the report shows the new prompt version.
2. **Connect (EXER038).** Add a trajectory category scored with the EXER038 functions. *Done when:* a simulated release with the same answers but four searches per question passes every answer category and fails the trajectory one.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER048/stretch/goal1_prompt_change.py
uv run python EXER048/stretch/goal2_trajectory_category.py
```
