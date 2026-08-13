"""Data models for the Claude Knowledge Graph Engineering Kit.

This file is the single source of truth for the kit's data contract. Every
persisted or LLM-produced structure is a Pydantic model defined here, and the
buyer-readable JSON Schemas in schemas/ are exported from these classes
(tools/export_schemas.py).

Design constraints worth knowing:

- Models that Claude fills via structured outputs avoid open dicts
  (``dict[str, str]``) because the structured-outputs feature requires
  ``additionalProperties: false`` on every object. Qualifiers and attributes
  are therefore typed key/value lists.
- Absence is not zero. Unknown values stay ``None``; nothing is silently
  defaulted to 0, "", or false at extraction time.
- Provenance is carried as verbatim quotes (``SourceSpan.quote``) rather than
  character offsets, because quotes can be deterministically re-verified
  against the source document while model-emitted offsets cannot.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0"

EntityType = Literal[
    "company", "product", "person", "location", "metric", "event", "other"
]

Uncertainty = Literal["stated", "implied", "uncertain"]


class KitModel(BaseModel):
    """Base for all kit models: unknown fields are rejected everywhere."""

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Source documents and provenance
# ---------------------------------------------------------------------------


class SourceDocument(KitModel):
    doc_id: str
    title: str
    text: str
    source_type: Optional[str] = None  # e.g. "press_release", "earnings_call"
    date: Optional[str] = None  # ISO date string when known


class SourceSpan(KitModel):
    """A citation locator: which document, and the verbatim supporting quote.

    ``quote`` must appear (whitespace-normalized) in the source document; the
    provenance module verifies this deterministically.
    """

    doc_id: str
    quote: str


# ---------------------------------------------------------------------------
# Stage 1 — Extraction
# ---------------------------------------------------------------------------


class Qualifier(KitModel):
    key: str
    value: str


class ScalarValue(KitModel):
    """A typed scalar object for facts like prices and margins.

    ``text`` is always the verbatim surface form; ``value``/``unit`` are
    filled only when the source states them, never invented.
    """

    kind: Literal["money", "percent", "number", "date", "text"]
    text: str
    value: Optional[float] = None
    unit: Optional[str] = None  # e.g. "USD/month", "USD", "pp"


class EntityMention(KitModel):
    surface_form: str
    entity_type: EntityType
    description: str  # short, source-grounded; used later for resolution
    span: SourceSpan


class CandidateFact(KitModel):
    """A candidate (subject, predicate, object) fact with provenance.

    Exactly one of ``object_entity`` / ``object_value`` should be set; the
    pipeline validates this deterministically after extraction.
    """

    subject: str  # surface form as written in this document
    predicate: str  # short snake_case relation, e.g. "changed_price"
    object_entity: Optional[str] = None
    object_value: Optional[ScalarValue] = None
    qualifiers: list[Qualifier] = Field(default_factory=list)
    time_context: Optional[str] = None
    uncertainty: Uncertainty = "stated"
    confidence: Optional[float] = None  # 0..1 when the model chooses to give one
    span: SourceSpan


class ExtractionResult(KitModel):
    doc_id: str
    mentions: list[EntityMention] = Field(default_factory=list)
    facts: list[CandidateFact] = Field(default_factory=list)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Stage 2 — Resolution
# ---------------------------------------------------------------------------


class EntityCluster(KitModel):
    """One canonical entity and the surface forms that refer to it."""

    canonical_name: str
    entity_type: EntityType
    members: list[str]  # surface forms merged into this entity
    rationale: str
    confidence: Optional[float] = None


class AmbiguousGroup(KitModel):
    """Surface forms that could not be safely merged or separated."""

    surface_forms: list[str]
    reason: str


class ResolutionResult(KitModel):
    clusters: list[EntityCluster] = Field(default_factory=list)
    ambiguous: list[AmbiguousGroup] = Field(default_factory=list)
    notes: Optional[str] = None


class ResolvedEntity(KitModel):
    """Deterministic post-processing of a cluster: canonical id assigned."""

    canonical_id: str
    canonical_name: str
    entity_type: EntityType
    aliases: list[str] = Field(default_factory=list)
    decision: Literal["merged", "single", "ambiguous"] = "single"
    rationale: Optional[str] = None
    confidence: Optional[float] = None
    provenance: list[SourceSpan] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 3 — Assembly (the persistent graph)
# ---------------------------------------------------------------------------


class Attribute(KitModel):
    key: str
    value: str


class Node(KitModel):
    node_id: str
    name: str
    entity_type: EntityType
    aliases: list[str] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    provenance: list[SourceSpan] = Field(default_factory=list)


class Edge(KitModel):
    edge_id: str
    subject_id: str
    predicate: str
    object_id: Optional[str] = None  # node id, XOR object_value
    object_value: Optional[ScalarValue] = None
    qualifiers: list[Qualifier] = Field(default_factory=list)
    time_context: Optional[str] = None
    uncertainty: Uncertainty = "stated"
    confidence: Optional[float] = None
    status: Literal["asserted", "superseded", "retracted"] = "asserted"
    citations: list[SourceSpan] = Field(default_factory=list)


class SourceRegistryEntry(KitModel):
    doc_id: str
    title: str
    sha256: str
    char_count: int


class KnowledgeGraph(KitModel):
    schema_version: str = SCHEMA_VERSION
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    sources: list[SourceRegistryEntry] = Field(default_factory=list)
    ambiguous: list[AmbiguousGroup] = Field(default_factory=list)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Stage 4 — Query
# ---------------------------------------------------------------------------


class QueryPlan(KitModel):
    """Semantic output: which entities/relations matter for a question."""

    entities: list[str]  # entity names or aliases to seed traversal from
    predicates: list[str] = Field(default_factory=list)  # empty = all
    max_hops: int = 2
    reasoning: str = ""


class EvidencePack(KitModel):
    """Deterministic traversal output handed to the answering model."""

    question: str
    seed_node_ids: list[str] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    rendered: str = ""  # human/model-readable serialization of the evidence


class Answer(KitModel):
    answer: str
    cited_edge_ids: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False


# ---------------------------------------------------------------------------
# Multi-agent layer
# ---------------------------------------------------------------------------


class AnalystFinding(KitModel):
    claim: str
    edge_ids: list[str]


class AnalystReport(KitModel):
    role: str
    question: str
    findings: list[AnalystFinding] = Field(default_factory=list)
    insufficient_evidence: bool = False
    notes: Optional[str] = None


class SynthesisReport(KitModel):
    assessment: str
    key_findings: list[AnalystFinding] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    caveats: Optional[str] = None


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class MetricResult(KitModel):
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int


class EvalRunRecord(KitModel):
    run_id: str
    timestamp: str
    suite: str
    engine: str
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, MetricResult] = Field(default_factory=dict)
    scalar_metrics: dict[str, float] = Field(default_factory=dict)
    details: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Deterministic helpers used across stages
# ---------------------------------------------------------------------------


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(name: str) -> str:
    """Stable ASCII slug for ids: 'Acme Corp.' -> 'acme-corp'."""
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    norm = norm.lower()
    norm = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")
    return norm or "unnamed"


def make_node_id(name: str, entity_type: str) -> str:
    return f"{entity_type}:{slugify(name)}"


def normalize_predicate(predicate: str) -> str:
    """Predicates are lowercase snake_case."""
    p = predicate.strip().lower()
    p = re.sub(r"[^a-z0-9]+", "_", p).strip("_")
    return p


def normalize_surface(surface: str) -> str:
    """Normalization for matching surface forms (NOT for merging entities).

    Lowercases, strips punctuation and common corporate suffixes. Two distinct
    companies can normalize identically — this is only used for exact-match
    lookups and alias indexing, never as sufficient evidence for a merge.
    """
    s = unicodedata.normalize("NFKD", surface).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    words = [w for w in s.split() if w not in _CORP_SUFFIXES]
    return " ".join(words) if words else s.strip()


_CORP_SUFFIXES = {"inc", "corp", "corporation", "co", "ltd", "llc", "plc"}
