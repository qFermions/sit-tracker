"""Provenance verification: quotes are checked, never trusted.

Every fact carries a verbatim quote from its source document. Because quotes
can be re-checked deterministically, provenance survives every stage: a claim
in the final answer traces to edges, edges to quotes, quotes to documents.
"""

from __future__ import annotations

import re
from typing import Optional

from kgkit.models import ExtractionResult, SourceDocument


# Curly quotes and long dashes are normalized so a model transcribing
# "Acme's" from a document containing "Acme’s" still verifies.
_PUNCT_MAP = str.maketrans(
    {"‘": "'", "’": "'", "“": '"', "”": '"',
     "–": "-", "—": "-", " ": " "}
)


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_PUNCT_MAP)).strip().lower()


def quote_in_doc(quote: str, doc_text: str) -> bool:
    """True when the quote appears in the document, ignoring whitespace, case,
    and curly-vs-straight punctuation.

    Note the honest limit (also in LIMITATIONS.md): this proves the quote
    EXISTS in the source, not that it semantically supports the fact. The
    minimum-length check in verify_extraction keeps trivially-true quotes
    ("the") from counting as provenance.
    """
    if not quote.strip():
        return False
    return _normalize_ws(quote) in _normalize_ws(doc_text)


MIN_QUOTE_WORDS = 3


def quote_too_short(quote: str) -> bool:
    return len(quote.split()) < MIN_QUOTE_WORDS


def verify_extraction(
    result: ExtractionResult, doc: SourceDocument
) -> list[str]:
    """Issues with an extraction result's provenance against its document."""
    issues: list[str] = []
    if result.doc_id != doc.doc_id:
        issues.append(
            f"extraction doc_id {result.doc_id!r} does not match document {doc.doc_id!r}"
        )
    for i, mention in enumerate(result.mentions):
        if mention.span.doc_id != doc.doc_id:
            issues.append(f"mention[{i}] cites wrong document {mention.span.doc_id!r}")
        elif not quote_in_doc(mention.span.quote, doc.text):
            issues.append(
                f"mention[{i}] ({mention.surface_form!r}) quote not found in source"
            )
        elif quote_too_short(mention.span.quote):
            issues.append(
                f"mention[{i}] quote is under {MIN_QUOTE_WORDS} words — too short "
                f"to be meaningful provenance; quote the surrounding phrase"
            )
    for i, fact in enumerate(result.facts):
        if fact.span.doc_id != doc.doc_id:
            issues.append(f"fact[{i}] cites wrong document {fact.span.doc_id!r}")
        elif not quote_in_doc(fact.span.quote, doc.text):
            issues.append(
                f"fact[{i}] ({fact.subject} --{fact.predicate}-->) quote not found"
            )
        elif quote_too_short(fact.span.quote):
            issues.append(
                f"fact[{i}] quote is under {MIN_QUOTE_WORDS} words — too short "
                f"to be meaningful provenance; quote the supporting sentence"
            )
        if (fact.object_entity is None) == (fact.object_value is None):
            issues.append(
                f"fact[{i}] must set exactly one of object_entity/object_value"
            )
    return issues


def salvage_extraction(
    result: ExtractionResult, doc: SourceDocument
) -> tuple[ExtractionResult, list[str]]:
    """Drop items whose provenance fails verification; report what was dropped.

    Used after the bounded repair loop is exhausted: bad items are removed
    rather than silently kept, and the drops are recorded.
    """
    dropped: list[str] = []
    mentions = []
    for m in result.mentions:
        if m.span.doc_id == doc.doc_id and quote_in_doc(m.span.quote, doc.text):
            mentions.append(m)
        else:
            dropped.append(f"dropped mention {m.surface_form!r} (unverifiable quote)")
    facts = []
    for f in result.facts:
        ok = (
            f.span.doc_id == doc.doc_id
            and quote_in_doc(f.span.quote, doc.text)
            and (f.object_entity is None) != (f.object_value is None)
        )
        if ok:
            facts.append(f)
        else:
            dropped.append(
                f"dropped fact {f.subject!r} --{f.predicate}--> (failed verification)"
            )
    clean = ExtractionResult(
        doc_id=doc.doc_id, mentions=mentions, facts=facts, notes=result.notes
    )
    return clean, dropped


def verify_citations(
    store, cited_edge_ids: list[str], allowed_edge_ids: Optional[set[str]] = None
) -> list[str]:
    """Check that cited edges exist (and, when given, were actually retrieved).

    ``allowed_edge_ids`` is the evidence pack shown to the model — citing an
    edge outside it means the claim was not grounded in retrieved evidence.
    """
    issues = []
    for eid in cited_edge_ids:
        edge = store.get_edge(eid)
        if edge is None:
            issues.append(f"cited edge {eid} does not exist in the graph")
            continue
        if allowed_edge_ids is not None and eid not in allowed_edge_ids:
            issues.append(f"cited edge {eid} was not part of the retrieved evidence")
        if not edge.citations:
            issues.append(f"cited edge {eid} has no source citations")
    return issues


def citation_report(store, cited_edge_ids: list[str]) -> str:
    """Human-readable trace: claim-supporting edges back to document quotes."""
    lines = []
    for eid in cited_edge_ids:
        edge = store.get_edge(eid)
        if edge is None:
            lines.append(f"[{eid}] MISSING FROM GRAPH")
            continue
        lines.append(store.render_edge(edge))
        for span in edge.citations:
            lines.append(f'    {span.doc_id}: "{span.quote}"')
    return "\n".join(lines)
