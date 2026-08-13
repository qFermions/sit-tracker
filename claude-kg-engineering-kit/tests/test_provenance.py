from kgkit.models import (
    CandidateFact,
    EntityMention,
    ExtractionResult,
    ScalarValue,
    SourceDocument,
    SourceSpan,
)
from kgkit.provenance import (
    quote_in_doc,
    salvage_extraction,
    verify_citations,
    verify_extraction,
)

DOC = SourceDocument(
    doc_id="d1",
    title="T",
    text="Acme raised the price\nof Widget from $5 to $9 per unit today.",
)


def test_quote_matching_ignores_whitespace_and_case():
    assert quote_in_doc("raised the price of Widget", DOC.text)
    assert quote_in_doc("RAISED THE PRICE", DOC.text)
    assert not quote_in_doc("lowered the price", DOC.text)
    assert not quote_in_doc("", DOC.text)


def _result(quote="from $5 to $9 per unit", doc_id="d1", both_objects=False):
    fact = CandidateFact(
        subject="Acme",
        predicate="changed_price",
        object_value=ScalarValue(kind="money", text="$9 per unit", value=9),
        object_entity="Widget" if both_objects else None,
        span=SourceSpan(doc_id=doc_id, quote=quote),
    )
    mention = EntityMention(
        surface_form="Acme",
        entity_type="company",
        description="widget maker",
        span=SourceSpan(doc_id=doc_id, quote="Acme raised the price"),
    )
    return ExtractionResult(doc_id="d1", mentions=[mention], facts=[fact])


def test_verify_extraction_accepts_good_provenance():
    assert verify_extraction(_result(), DOC) == []


def test_curly_punctuation_is_normalized():
    doc = "Acme’s “flagship” product — Widget — sells well."
    assert quote_in_doc('Acme\'s "flagship" product', doc)
    assert quote_in_doc("flagship” product — Widget", doc)


def test_trivially_short_quotes_are_flagged_as_weak_provenance():
    issues = verify_extraction(_result(quote="to $9"), DOC)  # 2 words, in doc
    assert any("too short" in i for i in issues)


def test_verify_extraction_catches_fabricated_quote():
    issues = verify_extraction(_result(quote="slashed prices dramatically"), DOC)
    assert any("quote not found" in i for i in issues)


def test_verify_extraction_catches_wrong_doc_and_double_object():
    issues = verify_extraction(_result(doc_id="d999"), DOC)
    assert any("wrong document" in i for i in issues)
    issues = verify_extraction(_result(both_objects=True), DOC)
    assert any("exactly one" in i for i in issues)


def test_salvage_drops_only_unverifiable_items():
    bad = _result(quote="totally invented text")
    clean, dropped = salvage_extraction(bad, DOC)
    assert clean.facts == []  # the bad fact is gone
    assert len(clean.mentions) == 1  # the good mention survives
    assert any("dropped fact" in d for d in dropped)


def test_full_provenance_chain_survives_to_the_graph(store, docs_by_id):
    """Every edge in the demo graph traces to a verbatim quote in a real doc."""
    assert store.graph.edges, "demo graph should have edges"
    for edge in store.graph.edges:
        assert edge.citations, f"{edge.edge_id} lost its provenance"
        for span in edge.citations:
            doc = docs_by_id[span.doc_id]
            assert quote_in_doc(span.quote, doc.text), (
                f"{edge.edge_id} cites a quote that is not in {span.doc_id}"
            )


def test_verify_citations_scopes_to_retrieved_evidence(store):
    some_edge = store.graph.edges[0].edge_id
    assert verify_citations(store, [some_edge]) == []
    assert verify_citations(store, ["e999"]) != []
    outside = verify_citations(store, [some_edge], allowed_edge_ids={"other"})
    assert any("not part of the retrieved evidence" in i for i in outside)
