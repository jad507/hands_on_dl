# Prompts

Each file here is the exact system prompt sent to the model, stored outside the
Python source so that a given output file can be traced back to the text that
produced it.

Every run records the SHA-256 of the prompt file it used, under `provenance` in
each output JSON. Given any file in `downloads/llm_outputs/`, you can therefore
determine which prompt produced it, which was not possible when these prompts
lived in string literals.

| File | Used by | Placeholders |
|---|---|---|
| `p1_system.txt` | Phase 1, public comment identification | none |
| `p2_system.txt` | Phase 2, theme scoring | `{themes_content}` |

`{themes_content}` is substituted by plain string replacement, not `str.format`,
so literal `{` and `}` in these files need no escaping. That matters because the
prompts contain JSON examples.

## Changing a prompt

Editing a file here changes its hash, which is the point: outputs produced
before and after the edit are distinguishable. If you are changing a prompt in a
way that makes old and new outputs non-comparable, say so in `NOTEBOOK.md` and
consider whether the affected outputs should be regenerated rather than mixed.

The full prompt actually sent also depends on the model's `no_think` setting,
which prepends a `/no_think` line. Outputs record `rendered_sha256` alongside the
file hash, which captures that and the substituted theme definitions.
