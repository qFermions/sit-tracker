<!-- version: 1 -->
# Track B — Run the knowledge-graph workflow inside a Claude Project

This is for buyers who don't want to run Python. You get the same staged
method — extraction, resolution, assembly, querying — as a disciplined
manual workflow inside one Claude Project.

**Honest scope first:** a Claude Project is a workspace with custom
instructions and project knowledge. It does **not** run this kit's Python,
does not call the API for you, and does not persist files between chats on
its own. In Track B, *you* are the pipeline's deterministic half: you keep
the graph JSON as a project knowledge file, and you paste stage outputs
forward. Claude does the semantic half. What the code track automates —
quote verification, citation checking, id assignment — you spot-check by
hand here (the instructions below tell Claude to make that easy for you).

## One-time setup

1. Create a Project (claude.ai → Projects). Paid plans include Projects;
   check your plan.
2. Paste the **Project instructions** block below into the project's
   custom instructions.
3. Upload to project knowledge:
   - `schemas/extraction.schema.json`, `schemas/resolution.schema.json`,
     `schemas/graph.schema.json` (so Claude has the exact shapes),
   - your source documents, each with a clear id (`d1`, `d2`, …),
   - `graph.json` once it exists (re-upload after each update — Projects
     don't let Claude persist edits to knowledge files).

## Project instructions (paste verbatim)

```
You operate a staged knowledge-graph workflow. Work in exactly one stage
per request, always returning JSON valid against the uploaded schemas.

Rules that apply to every stage:
- Only report what the source documents actually say. Absence is not zero;
  unknown is not false. Unknown fields stay null.
- Every mention/fact carries doc_id and a VERBATIM quote from that
  document. After any JSON output, list each quote on its own line so the
  user can spot-check it with Ctrl+F in the source.
- Never merge entities on name similarity alone; keep genuine ambiguity in
  the "ambiguous" list with a reason.
- When asked to ANSWER a question: use only the edges of the uploaded
  graph.json, cite edge ids for every material claim, and if the graph
  lacks the facts, answer exactly "Insufficient evidence" plus what is
  missing. Never fill gaps from your general knowledge.

Stages you accept:
1. EXTRACT <doc_id> — output extraction.schema JSON for that document.
2. RESOLVE — input: all mentions so far; output resolution.schema JSON.
3. ASSEMBLE — input: extractions + resolution; output graph.schema JSON
   with node_ids like "company:acme", sequential edge ids e001…, every
   edge carrying its citations. This is bookkeeping: invent nothing.
4. QUERY <question> — plan (entities, relations, hops), then list the
   relevant edges from graph.json, then answer with [edge id] citations.
5. ANALYST <role> — answer that role's bounded question from graph.json
   edges only, findings each citing edge ids.
6. SYNTHESIZE — combine the analyst reports just given in this chat into
   one assessment; every load-bearing claim cites edge ids; state caveats.
```

## The working loop

1. New chat: `EXTRACT d1` … one message per document. Save each JSON
   locally.
2. `RESOLVE` — paste the mention lists (or point Claude at the extraction
   outputs earlier in the chat).
3. `ASSEMBLE` — paste extractions + resolution; save the output as
   `graph.json` and **upload it to project knowledge**.
4. New chats can now just ask: `QUERY why did X raise prices?` — Claude
   reads graph.json from project knowledge and answers with edge citations.
5. For the multi-agent pattern: one message per `ANALYST pricing`,
   `ANALYST product`, `ANALYST financial`, then `SYNTHESIZE` in the same
   chat.

## Manual vs automatic — the honest split

| Step | Track A (code) | Track B (Projects) |
|---|---|---|
| Extraction / resolution / answering | Claude via API | Claude in chat |
| Quote verification | automatic, machine-checked | you, Ctrl+F spot-checks |
| Id assignment, dedupe, validation | deterministic code | Claude follows rules; you review |
| Graph persistence | graph.json written by the kit | you save + re-upload graph.json |
| Citation checking | automatic, invalid cites stripped | you confirm edge ids exist |
| Evaluation harness | `kgkit eval run` / `compare` | manual: keep a small Q&A list and re-ask after prompt changes |

If you find yourself doing the right column daily, that is the signal to
move to Track A — the method transfers unchanged.
