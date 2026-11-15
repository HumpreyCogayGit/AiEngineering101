# EXER042 — Identity and Tenant Boundaries

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec042.html](../Lecture/lectures/lec042.html)

## Goal

Make the EXER041 service safe for more than one user: every request is authenticated, and a user can
only reach their own conversations, their own notes and the documents they may read.

## The project

| File | Status | Your work |
|---|---|---|
| `secure_service.py` | TODO | `bearer_token`, `authenticate`, `thread_key`, `notes_file`, `search_filter`, `permitted_search`, `route` |

`TokenStore`, the HTTP plumbing and `UserHelpdesks` (one EXER037 assistant per user, with that user's
notes file and search filter) are given. Liveness, readiness and configuration come unchanged from the
EXER041 reference service.

| Route | Token | Answers |
|---|---|---|
| `GET /healthz`, `GET /readyz` | no | as in EXER041 |
| `POST /ask` | yes | `{"question": "...", "thread_id": "optional"}` → the reply. The user comes from the token |
| `GET /threads/<id>` | yes | your own conversation, or 404 |

## Run it

```bash
uv run python EXER042/starter/secure_service.py issue ana customer   # prints a token once; stores only its hash
uv run python EXER042/starter/secure_service.py issue ben staff
set -a; source .env; set +a
uv run python EXER042/starter/secure_service.py
curl -X POST localhost:8000/ask -H "Authorization: Bearer <ana's token>" \
     -d '{"question": "How many vacation days do employees get?", "thread_id": "t1"}'
curl localhost:8000/threads/t1 -H "Authorization: Bearer <ben's token>"     # 404
uv run python EXER042/check.py
```

## Success criteria

- [ ] Without a valid token every route except the health checks answers 401 with a `WWW-Authenticate` header
- [ ] A `user_id` in the request body is ignored: the user comes from the token
- [ ] User B gets 404 for user A's thread, and B's questions with A's thread id go to B's own conversation
- [ ] Thread ids and user ids with `/` or `..` are rejected, so a key can never point outside its namespace
- [ ] A customer's search never returns the employee handbook; a staff member's does
- [ ] All 9 checks pass (one is `[live API]`: it searches the real index)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Authorize tools by role: customers may search and calculate, only staff may use the notes tools. *Done when:* the same "save a note" request writes a note for a staff member and cannot for a customer, because the customer's assistant never receives the tool.
2. **Connect (EXER028).** Store conversations in SQLite so they survive a restart. *Done when:* after a restart, user A can read and continue their thread and user B still gets 404 for it.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER042/stretch/goal1_tool_permissions.py
uv run python EXER042/stretch/goal2_durable_threads.py
```
