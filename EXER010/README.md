# EXER010 — Building a CLI App

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec010.html](../Lecture/lectures/lec010.html)

## Goal

Package what you have learned into a proper command-line tool with
sub-commands, options, stdin piping, streaming output and meaningful exit codes.

## The project

`ask.py`, built with [Typer](https://typer.tiangolo.com):

| Command | Example |
|---|---|
| `ask` | `ask.py ask "What is RAG?" --system "Be brief" -t 0.2` |
| `chat` | `ask.py chat` |
| `summarize` | `ask.py summarize notes.txt --words 50` or `cat notes.txt \| ask.py summarize -` |

## Tasks

Complete the TODOs in `starter/ask.py`: `stream_answer`, the `ask` command,
`read_input`, and the `summarize` command (including registering it).

## Run it

```bash
uv run python EXER010/starter/ask.py --help
uv run python EXER010/starter/ask.py ask "Tell me a joke"
uv run python EXER010/check.py
```

## Success criteria

- [ ] `--help` shows all three commands with descriptions
- [ ] Answers stream to the terminal
- [ ] Piping text into `summarize -` works
- [ ] A missing file prints an error to stderr and exits with code `1`
- [ ] All 6 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a `--json` flag to `ask` that prints one machine-readable object instead of streaming text. *Done when:* the output pipes cleanly into `python -m json.tool`.
2. **Connect (EXER008).** Add a `classify` command that reuses the EXER008 prompt. *Done when:* the command prints one label and nothing else, for an argument and for piped input.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER010/stretch/goal1_json_flag.py ask "What is RAG?" --json
uv run python EXER010/stretch/goal2_classify_command.py classify "I was charged twice"
```
