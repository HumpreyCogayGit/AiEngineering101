# EXER045 — Caching and Batch Work

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec045.html](../Lecture/lectures/lec045.html)

## Goal

Pay less for the same answers without serving wrong ones: an exact-match response cache with a key that
cannot leak across tenants or roles, a prompt layout the provider can reuse, and requests packaged for a
batch endpoint.

## The project

| File | Status | Your work |
|---|---|---|
| `caching.py` | TODO | `normalize`, `cache_key`, `ResponseCache.get`, `cacheable`, `build_messages`, `batch_lines` |
| `prefix_experiment.py` | given | measures the cached prompt tokens your provider reports, for two layouts |

`CachedHelpdesk` (the cache in front of the EXER042 per-user helpdesk) is given and uses your functions.

## Run it

```bash
uv run python EXER045/starter/caching.py              # five questions through the cache (live)
uv run python EXER045/starter/prefix_experiment.py    # stable vs unstable prompt layout (live)
uv run python EXER045/check.py
```

## Success criteria

- [ ] The cache key changes when the model, prompt version, tools, policy, tenant or role changes, and not for case, spacing or trailing punctuation
- [ ] Expired entries are removed and counted; hits, misses and the hit rate are reported
- [ ] Blocked replies, follow-up turns and answers that saved something are never cached
- [ ] Two customers on two days send prompts that are identical up to the volatile part
- [ ] `prefix_experiment.py` shows cached prompt tokens for the stable layout from the second call on (on a provider that reports them)
- [ ] All 8 checks pass (one is `[live API]`: it shows with your embedding model why a semantic cache is unsafe)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Put a version of the knowledge base into the cache key. *Done when:* in a simulated week where a policy document changes on day 3, the versioned cache serves no stale answers, and the script prints how many a TTL-only cache served.
2. **Connect (EXER040).** Measure which layout of the EXER040 context lets your provider reuse the prefix. *Done when:* the script prints the cached tokens per call for three layouts, with a never-seen question each time.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER045/stretch/goal1_kb_versioned_cache.py
uv run python EXER045/stretch/goal2_context_prefix.py
```
