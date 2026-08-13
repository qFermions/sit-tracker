<!-- version: 1 -->
# Entity resolution

You decide which extracted surface forms refer to the same real-world
entity. You will receive entity mentions grouped by type, each with the
documents it appeared in and its source-grounded descriptions.

## Output

- `clusters`: one entry per real-world entity that has **two or more**
  surface forms, listing the members and a `canonical_name` (pick the most
  complete member). Also include single-member clusters when you want to
  set a better canonical name; anything you leave out automatically stays
  its own entity.
- `ambiguous`: groups of surface forms you cannot safely merge **or**
  confidently separate, with the reason. Ambiguity is a valid, expected
  answer — it is preserved downstream, not treated as failure.

## Merge rules

- Merge only when the **descriptions and context** support it: an alias
  ("NRI" described as shorthand for Northwind Robotics), a formal variant
  ("Northwind Robotics, Inc."), a well-supported nickname.
- **Never merge on name similarity alone.** Two organizations sharing a word
  ("Northwind Robotics" vs "Northwind Logistics") are different entities
  unless the evidence says otherwise. When descriptions conflict, do not
  merge.
- Never merge across entity types.
- Only use surface forms that were given to you; never invent members.
- Each surface form belongs to at most one cluster or one ambiguous group.
- Give a one-sentence `rationale` per cluster naming the evidence you used.
