"""
Equine Health RAG Module
Retrieves veterinary knowledge from 'equine_database' Qdrant collection and
fuses it with multimodal sensor + behavior data to produce clinical assessments.
"""

from __future__ import annotations

import re
from typing import List, Optional, Any, Dict, Tuple

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client import models as qdrant_models
from pydantic import BaseModel, Field
import torch

# ─── Configuration ────────────────────────────────────────────────────────────
QDRANT_URL        = "http://localhost:6333"
COLLECTION_NAME   = "equine_database"
EMBEDDING_MODEL   = "BAAI/bge-base-en-v1.5"
RERANKER_MODEL    = "cross-encoder/ms-marco-MiniLM-L-6-v2"
# Fetch this many candidates from Qdrant before re-ranking down to top_k
RERANK_CANDIDATES = 15
# Minimum cosine similarity score to keep a retrieved chunk
MIN_SCORE_THRESHOLD = 0.20   # lowered from 0.30 — domain-specific medical text has lower cosine scores


# ─── Data Models ──────────────────────────────────────────────────────────────

class SensorData(BaseModel):
    """Hardware sensor readings from ESP32 wearable / environmental sensors."""
    heart_rate:       Optional[float] = Field(None, description="BPM — normal 28-44")
    temperature_c:    Optional[float] = Field(None, description="°C — normal 37.2-38.5")
    respiratory_rate: Optional[float] = Field(None, description="breaths/min — normal 8-16")
    hrv_sdnn:         Optional[float] = Field(None, description="HRV SDNN ms — healthy > 50ms")
    hrv_rmssd:        Optional[float] = Field(None, description="HRV RMSSD ms — low < 20 = stress")
    humidity_pct:     Optional[float] = Field(None, description="Ambient humidity %")
    ambient_temp_c:   Optional[float] = Field(None, description="Ambient temperature °C")


class BehaviorData(BaseModel):
    """
    Outputs from the CV pipeline (VAME + VLM + DLC).
    vame_motif:   VAME cluster label  e.g. 'rolling', 'pawing', 'grazing'
    vlm_state:    VLM classifier output  e.g. 'lying', 'eating', 'standing'
    hgs_score:    Horse Grimace Scale 0-10 (from keypoint / VLM analysis)
    duration_min: Minutes the current behavior has been continuously observed
    """
    vame_motif:       Optional[str]   = Field(None)
    vlm_state:        Optional[str]   = Field(None)
    hgs_score:        Optional[float] = Field(None, ge=0, le=10)
    duration_min:     Optional[float] = Field(None)
    additional_notes: Optional[str]   = Field(None)


class AssessmentResult(BaseModel):
    """Structured clinical assessment output from HorseRAG.assess()."""
    urgency:             int        = Field(..., ge=1, le=5, description="Triage level 1-5")
    call_vet:            bool       = Field(...)
    possible_conditions: List[str]  = Field(default_factory=list)
    diagnosis_summary:   str        = Field(default="")
    immediate_actions:   List[str]  = Field(default_factory=list)
    monitoring_tips:     List[str]  = Field(default_factory=list)
    confidence:          float      = Field(default=0.5, ge=0.0, le=1.0)
    retrieved_sources:   List[str]  = Field(default_factory=list)
    raw_llm_response:    str        = Field(default="")
    retrieval_time_s:    float      = Field(default=0.0, description="Seconds spent on vector retrieval")
    llm_time_s:          float      = Field(default=0.0, description="Seconds spent on LLM generation")


# ─── HorseRAG ─────────────────────────────────────────────────────────────────

class HorseRAG:
    """
    Retrieval-Augmented Generation layer for equine health assessment.

    Connects to the 'equine_database' Qdrant collection, retrieves relevant
    veterinary knowledge chunks based on sensor + behavior inputs, and augments
    the HorseExpertAgent prompt to produce a structured clinical assessment.
    """

    def __init__(
        self,
        qdrant_url:       str = QDRANT_URL,
        collection_name:  str = COLLECTION_NAME,
        embedding_model:  str = EMBEDDING_MODEL,
        reranker_model:   str = RERANKER_MODEL,
        top_k:            int = 5,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        use_reranker:     bool = True,
    ) -> None:
        self.collection_name = collection_name
        self.top_k           = top_k
        self.use_reranker    = use_reranker
        self._device         = device

        gpu_label = ""
        if device == "cuda" and torch.cuda.is_available():
            gpu_label = f" ({torch.cuda.get_device_name(0)})"
        print(f"  Embeddings device : {device.upper()}{gpu_label}")

        self._embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
        self._client = QdrantClient(url=qdrant_url)
        self._vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
            embedding=self._embeddings,
        )
        self._retriever = self._vector_store.as_retriever(
            search_kwargs={"k": RERANK_CANDIDATES if use_reranker else top_k}
        )

        self._reranker = None
        if use_reranker:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(reranker_model)
            except Exception as exc:
                print(f"[HorseRAG] Re-ranker unavailable ({exc}); falling back to similarity order.")
                self.use_reranker = False

    def build_query(
        self,
        sensors:    SensorData,
        behavior:   BehaviorData,
        breed:      Optional[str] = None,
        horse_age:  Optional[int] = None,
    ) -> str:
        parts: List[str] = []

        if breed:
            parts.append(f"horse breed {breed}")
        if horse_age is not None:
            label = "foal" if horse_age < 1 else ("geriatric" if horse_age > 18 else "adult")
            parts.append(f"{label} horse age {horse_age} years")

        if behavior.vame_motif:
            parts.append(f"horse behavior {behavior.vame_motif}")
        if behavior.vlm_state:
            state = behavior.vlm_state.lower()
            if state in ("lying", "rolling"):
                parts.append("recumbent horse abdominal pain")
            elif state == "eating":
                parts.append("horse eating pattern appetite inappetence")
            parts.append(f"horse state {state}")
        if behavior.hgs_score is not None and behavior.hgs_score >= 4:
            parts.append("horse grimace scale pain facial expression")
        if behavior.duration_min is not None and behavior.duration_min > 30:
            parts.append(f"prolonged {behavior.vame_motif or behavior.vlm_state} duration")
        if behavior.additional_notes:
            parts.append(behavior.additional_notes)

        combined_text = " ".join([
            behavior.vame_motif or "",
            behavior.vlm_state or "",
            behavior.additional_notes or "",
        ]).lower()
        breed_lower = (breed or "").lower()

        if "quarter" in breed_lower:
            if any(kw in combined_text for kw in ["twitch", "fascicul", "tremor", "weakness", "collapse", "paralysis"]):
                parts.append("HYPP hyperkalemic periodic paralysis muscle fasciculation Quarter Horse")
            if any(kw in combined_text for kw in ["stiff", "tying", "reluctan", "sweat", "dark urine", "myoglobin"]):
                parts.append("PSSM polysaccharide storage myopathy tying-up Quarter Horse")
            if any(kw in combined_text for kw in ["skin", "tear", "wound", "peel"]):
                parts.append("HERDA hereditary equine regional dermal asthenia")

        elif "thoroughbred" in breed_lower or "tb" in breed_lower:
            if any(kw in combined_text for kw in ["bleed", "blood", "nostril", "epistaxis", "cough"]):
                parts.append("EIPH exercise induced pulmonary hemorrhage Thoroughbred")
            if any(kw in combined_text for kw in ["appetite", "girth", "eat", "weight loss", "yawn", "grind"]):
                parts.append("EGUS equine gastric ulcer syndrome Thoroughbred")
            if any(kw in combined_text for kw in ["irregular", "arrhyth"]):
                parts.append("atrial fibrillation Thoroughbred heart arrhythmia")

        elif "arab" in breed_lower:
            if any(kw in combined_text for kw in ["atax", "tremor", "incoord", "wide"]):
                parts.append("cerebellar abiotrophy Arabian ataxia")
            if horse_age is not None and horse_age < 1:
                parts.append("SCID severe combined immunodeficiency Arabian foal")

        if sensors.heart_rate is not None:
            parts.append(f"horse heart rate {sensors.heart_rate:.0f} bpm")
            if sensors.heart_rate > 60:
                parts.append("elevated heart rate severe pain colic emergency")
            elif sensors.heart_rate > 50:
                parts.append("elevated heart rate horse discomfort")
        if sensors.temperature_c is not None:
            parts.append(f"horse temperature {sensors.temperature_c:.1f} Celsius")
            if sensors.temperature_c > 40.0:
                parts.append("horse fever high temperature infection")
        if sensors.respiratory_rate is not None:
            parts.append(f"horse respiratory rate {sensors.respiratory_rate:.0f} breaths per minute")
            if sensors.respiratory_rate > 30:
                parts.append("respiratory distress labored breathing")
        if sensors.hrv_rmssd is not None and sensors.hrv_rmssd < 20:
            parts.append("horse heart rate variability low stress sympathetic nervous system")

        query = " ".join(parts)
        words = query.split()
        if len(words) > 150:
            query = " ".join(words[:150])
        return query

    @staticmethod
    def _build_breed_filter(breed: Optional[str]) -> Optional[qdrant_models.Filter]:
        if not breed:
            return None

        breed_lower = breed.lower()
        breed_category: Optional[str] = None
        if "quarter" in breed_lower:
            breed_category = "quarter_horse_breed"
        elif "thoroughbred" in breed_lower or " tb" in breed_lower:
            breed_category = "thoroughbred_breed"
        elif "arab" in breed_lower:
            breed_category = "arabian_breed"

        general_categories = ["merck", "madbarn", "universities", "other"]
        categories = general_categories + ([breed_category] if breed_category else [])

        return qdrant_models.Filter(
            should=[
                qdrant_models.FieldCondition(
                    key="metadata.category",
                    match=qdrant_models.MatchValue(value=cat),
                )
                for cat in categories
            ]
        )

    def _rerank(self, query: str, docs: List[Document], keep: int) -> List[Document]:
        if not self._reranker or not docs:
            return docs[:keep]

        passages = [d.page_content for d in docs]
        scores: List[float] = self._reranker.predict(
            [[query, p] for p in passages]
        ).tolist()

        scored: List[Tuple[float, Document]] = sorted(
            zip(scores, docs), key=lambda x: x[0], reverse=True
        )
        for score, doc in scored:
            doc.metadata["rerank_score"] = round(score, 4)

        return [doc for _, doc in scored[:keep]]

    def retrieve(
        self,
        query:  str,
        k:      Optional[int] = None,
        filter: Optional[qdrant_models.Filter] = None,
    ) -> List[Document]:
        final_k    = k if k is not None else self.top_k
        candidates = RERANK_CANDIDATES if self.use_reranker else final_k

        search_kwargs: Dict[str, Any] = {"k": candidates}
        if filter is not None:
            search_kwargs["filter"] = filter

        scored_docs = self._vector_store.similarity_search_with_score(
            query, **search_kwargs
        )

        docs = [doc for doc, score in scored_docs if score >= MIN_SCORE_THRESHOLD]

        if not docs and filter is not None:
            scored_docs = self._vector_store.similarity_search_with_score(
                query, k=candidates
            )
            docs = [doc for doc, score in scored_docs if score >= MIN_SCORE_THRESHOLD]

        if not docs:
            docs = [doc for doc, _ in scored_docs]

        if self.use_reranker:
            return self._rerank(query, docs, keep=final_k)

        return docs[:final_k]

    def collection_info(self) -> Dict[str, Any]:
        info = self._client.get_collection(self.collection_name)
        return {
            "collection":  self.collection_name,
            "points_count": info.points_count,
            "status":       str(info.status),
        }

    def __repr__(self) -> str:
        return f"HorseRAG(collection='{self.collection_name}', top_k={self.top_k})"


# ─── Private Parse Helpers ────────────────────────────────────────────────────

def _parse_json_response(text: str) -> dict:
    import json as _json

    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()

    try:
        data = _json.loads(clean)
        if isinstance(data, dict):
            if "urgency" in data:
                data["urgency"] = max(1, min(5, int(data["urgency"])))
            return data
    except (_json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{[\s\S]*\}", clean)
    if match:
        try:
            data = _json.loads(match.group())
            if isinstance(data, dict):
                if "urgency" in data:
                    data["urgency"] = max(1, min(5, int(data["urgency"])))
                return data
        except (_json.JSONDecodeError, ValueError):
            pass

    return {}


def _format_sensors(s: SensorData) -> str:
    lines = []
    if s.heart_rate is not None:
        flag = " ⚠️" if s.heart_rate > 50 else " ✓"
        lines.append(f"- Heart Rate:       {s.heart_rate:.0f} bpm{flag}   (normal 28-44)")
    if s.temperature_c is not None:
        flag = " ⚠️" if s.temperature_c > 38.9 else " ✓"
        lines.append(f"- Temperature:      {s.temperature_c:.1f} °C{flag}   (normal 37.2-38.5)")
    if s.respiratory_rate is not None:
        flag = " ⚠️" if s.respiratory_rate > 20 else " ✓"
        lines.append(f"- Respiratory Rate: {s.respiratory_rate:.0f}/min{flag}   (normal 8-16)")
    if s.hrv_sdnn is not None:
        lines.append(f"- HRV SDNN:         {s.hrv_sdnn:.1f} ms   (healthy > 50 ms)")
    if s.hrv_rmssd is not None:
        flag = " ⚠️" if s.hrv_rmssd < 20 else " ✓"
        lines.append(f"- HRV RMSSD:        {s.hrv_rmssd:.1f} ms{flag}   (stress < 20 ms)")
    if s.ambient_temp_c is not None:
        lines.append(f"- Ambient Temp:     {s.ambient_temp_c:.1f} °C")
    if s.humidity_pct is not None:
        lines.append(f"- Humidity:         {s.humidity_pct:.0f} %")
    return "\n".join(lines) if lines else "_No sensor readings provided_"


def _format_behavior(b: BehaviorData) -> str:
    lines = []
    if b.vame_motif:
        lines.append(f"- VAME Motif:  {b.vame_motif}")
    if b.vlm_state:
        lines.append(f"- VLM State:   {b.vlm_state}")
    if b.hgs_score is not None:
        label = "severe" if b.hgs_score >= 7 else ("moderate" if b.hgs_score >= 4 else "mild")
        lines.append(f"- HGS Score:   {b.hgs_score}/10 ({label} pain)")
    if b.duration_min is not None:
        lines.append(f"- Duration:    {b.duration_min:.0f} min")
    if b.additional_notes:
        lines.append(f"- Notes:       {b.additional_notes}")
    return "\n".join(lines) if lines else "_No behavior data provided_"


def _parse_urgency(text: str) -> int:
    lower = text.lower()

    matches = re.findall(r"urgency[\s]*(?:level)?[:\s#*]*([1-5])(?:\s*/\s*5)?", lower)
    if matches:
        return int(matches[0])

    level_matches = re.findall(r"(?:^|\n)\s*[-•*]?\s*level\s*([1-5])", lower)
    if level_matches:
        return int(level_matches[0])

    def _has_keyword(keywords: list) -> bool:
        for kw in keywords:
            idx = lower.find(kw)
            if idx == -1:
                continue
            prefix = lower[max(0, idx - 30):idx]
            if any(neg in prefix for neg in ["no ", "not ", "isn't", "not a", "no need",
                                              "don't", "doesn't", "without", "unlikely"]):
                continue
            return True
        return False

    if _has_keyword(["call vet immediately", "do not wait", "act now"]):
        return 5
    if _has_keyword(["same-day vet", "urgent vet", "call your vet today"]):
        return 4
    if _has_keyword(["vet visit within", "schedule a vet", "within 24-48"]):
        return 3
    return 1


def _parse_conditions(text: str) -> List[str]:
    keywords = [
        "HYPP", "hyperkalemic periodic paralysis",
        "PSSM", "polysaccharide storage myopathy",
        "HERDA", "GBED", "SCID", "cerebellar abiotrophy",
        "EIPH", "pulmonary hemorrhage",
        "EGUS", "gastric ulcer",
        "atrial fibrillation", "OCD", "osteochondrosis",
        "navicular", "bucked shins",
        "colic", "laminitis", "lameness", "strangles", "pneumonia",
        "PPID", "Cushing", "infection", "dehydration", "heat stroke",
        "EPM", "abscess", "tying-up", "rhabdomyolysis", "EMS",
        "enteritis", "impaction", "colitis",
    ]
    lower = text.lower()
    found = []
    seen = set()
    for kw in keywords:
        if kw.lower() in lower and kw.lower() not in seen:
            found.append(kw)
            seen.add(kw.lower())
            if kw == "HYPP":
                seen.add("hyperkalemic periodic paralysis")
            elif kw == "hyperkalemic periodic paralysis":
                seen.add("hypp")
            elif kw == "PSSM":
                seen.add("polysaccharide storage myopathy")
            elif kw == "EIPH":
                seen.add("pulmonary hemorrhage")
            elif kw == "EGUS":
                seen.add("gastric ulcer")
            elif kw == "gastric ulcer":
                seen.add("egus")
    return found[:6]


def _parse_actions(text: str) -> List[str]:
    lines, actions, capture = text.split("\n"), [], False
    for line in lines:
        stripped = line.strip()
        if any(h in stripped.lower() for h in ["immediate action", "right now", "what to do", "first aid"]):
            capture = True
            continue
        if capture and re.match(r"^[-•*\d]", stripped):
            clean = re.sub(r"^[-•*\d.]\s*", "", stripped)
            if clean:
                actions.append(clean)
        if capture and stripped == "" and actions:
            break
    return actions[:6]


def _parse_monitoring(text: str) -> List[str]:
    lines, tips, capture = text.split("\n"), [], False
    for line in lines:
        stripped = line.strip()
        if any(h in stripped.lower() for h in ["monitor", "watch for", "tip", "track"]):
            capture = True
            continue
        if capture and re.match(r"^[-•*]", stripped):
            clean = re.sub(r"^[-•*]\s*", "", stripped)
            if clean:
                tips.append(clean)
        if capture and stripped == "" and tips:
            break
    return tips[:5]


def _estimate_confidence(docs: List[Document], urgency: int) -> float:
    doc_score = min(len(docs) / 5.0, 1.0)

    rerank_scores = [
        d.metadata["rerank_score"]
        for d in docs
        if "rerank_score" in d.metadata
    ]
    if rerank_scores:
        import math
        def _sigmoid(x: float) -> float:
            return 1.0 / (1.0 + math.exp(-x))
        score_mean = sum(_sigmoid(s) for s in rerank_scores) / len(rerank_scores)
        doc_score = (doc_score + score_mean) / 2.0

    penalty = (urgency - 1) * 0.05
    return max(0.1, round(doc_score - penalty, 2))
