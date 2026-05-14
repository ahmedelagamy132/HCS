"""
Horse Expert Agent — central LLM orchestrator for EquiMonitor.

Flag summary
------------
  use_rag      Retrieve from Qdrant before every ask/assess call
  use_sensors  Include hardware sensor readings (HR, temp, RR, HRV) in prompts
  use_behavior Include CV pipeline outputs (VAME, VLM, HGS) in prompts
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, List

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

if TYPE_CHECKING:
    from app.services.horse_rag import SensorData, BehaviorData, AssessmentResult, HorseRAG

_DEFAULT_NUM_CTX = 6144


class HorseExpertAgent:
    """
    Expert horse care AI agent — the single entry-point for all LLM work.

    Modes are controlled by three boolean flags set at construction or changed
    at runtime with set_mode():

      use_rag=True, use_sensors=True, use_behavior=True   → full mode
      use_rag=False                                        → LLM-only (no Qdrant)
    """

    def __init__(
        self,
        model_name:   str = "qwen3.5:9b",
        temperature:  float = 0.7,
        history_file: Optional[str] = None,
        use_rag:      bool = True,
        use_sensors:  bool = True,
        use_behavior: bool = True,
    ):
        self.model_name          = model_name
        self.default_temperature = temperature
        self.use_rag             = use_rag
        self.use_sensors         = use_sensors
        self.use_behavior        = use_behavior

        self.chat_model = ChatOllama(
            model=model_name,
            temperature=temperature,
            num_ctx=_DEFAULT_NUM_CTX,
            reasoning=False,
        )
        self.history       = InMemoryChatMessageHistory()
        self.output_parser = StrOutputParser()

        self._rag: Optional["HorseRAG"] = None

        if history_file and Path(history_file).exists():
            self.load_history(history_file)

        self.chain = self._create_chain()

        if use_rag:
            try:
                from app.services.horse_rag import HorseRAG as _HorseRAG
                self._rag = _HorseRAG()
            except Exception as exc:
                print(f"[WARN] RAG engine unavailable ({exc}). Running in LLM-only mode.")
                self.use_rag = False

    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", self._system_prompt()),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{question}"),
        ])

    def _system_prompt(self) -> str:
        base = """
### ROLE & CONTEXT
You are an AI assistant specialized in the EquiMonitor system - an intelligent horse stable monitoring solution that uses computer vision and AI to provide 24/7 automated observation of horses.

### YOUR EXPERTISE
You are deeply knowledgeable about:
1. **EquiMonitor System Features:**
   - Real-time behavior monitoring using computer vision
   - Abnormality detection in movement and posture
   - Disease detection (colic, lameness) through AI analysis
   - Eating and drinking pattern analysis
   - Intruder detection and security alerts
   - Birth notification system
   - Automated daily training reports
   - Data-driven insights for stable management

2. **Equine Health & Behavior:**
   - Signs and symptoms of colic, lameness, and other conditions
   - Normal vs. abnormal eating/drinking patterns
   - Behavioral indicators of distress or illness
   - Posture analysis and movement assessment
   - Birth signs and foaling process

3. **Technology Integration:**
   - How AI/computer vision works in stable monitoring
   - Camera placement and system setup
   - Alert systems and notification protocols
   - Data interpretation and reporting

### INSTRUCTIONS
1. Provide expert guidance on horse health monitoring and EquiMonitor features
2. Explain how AI/computer vision detects specific conditions
3. Offer actionable advice based on monitoring data and alerts
4. Emphasize early detection and preventive care
5. **STRICT RAG INTEGRATION:** When veterinary context blocks are retrieved from the knowledge base, you MUST base your medical descriptions ONLY on that text. Retain the exact clinical terminology. Do NOT simplify or substitute with generic or human anatomical terms.
6. **FORMATTING:** Always use Markdown (bold, lists, headings) for readability.

### GUARDRAILS AND CONSTRAINTS
- **SCOPE:** Only answer questions related to horse health, EquiMonitor features, stable management, and veterinary monitoring.
- **NO HALLUCINATIONS:** Never invent clinical symptoms, features, or anatomies. If the retrieved context does not contain the answer, explicitly state: "I do not have that specific clinical detail in my knowledge base."
- **REFUSAL PROTOCOL:** For unrelated topics respond: "I am specialized exclusively in equine health monitoring and the EquiMonitor system."
"""
        channels: List[str] = []
        if self.use_sensors:
            channels.append("Hardware sensor readings (heart rate, temperature, respiratory rate, HRV)")
        if self.use_behavior:
            channels.append("CV pipeline outputs (VAME motif, VLM posture state, HGS pain score)")
        if self.use_rag and self._rag is not None:
            channels.append("Veterinary knowledge base (RAG — retrieved from Qdrant)")

        if channels:
            footer = "\n### ACTIVE DATA CHANNELS FOR THIS SESSION\n" + "\n".join(f"- {c}" for c in channels)
            footer += "\nWhen clinical data appears in a message, use it. Do not invent data that was not provided."
        else:
            footer = (
                "\n### ACTIVE DATA CHANNELS FOR THIS SESSION\n"
                "No live sensor or behavioural data is active. "
                "Answer based on general equine knowledge and the EquiMonitor system context only."
            )
        return base + footer

    _CLINICAL_SYSTEM = (
        "You are a veterinary AI assistant. "
        "Respond with ONLY a valid JSON object matching the exact schema provided. "
        "No markdown fences, no prose, no explanation outside the JSON."
    )

    def _create_chain(self):
        return self._build_prompt_template() | self.chat_model | self.output_parser

    def set_mode(
        self,
        use_rag:      Optional[bool] = None,
        use_sensors:  Optional[bool] = None,
        use_behavior: Optional[bool] = None,
    ) -> None:
        if use_rag is not None and use_rag != self.use_rag:
            self.use_rag = use_rag
            if use_rag and self._rag is None:
                try:
                    from app.services.horse_rag import HorseRAG as _HorseRAG
                    self._rag = _HorseRAG()
                except Exception as exc:
                    print(f"[WARN] RAG engine unavailable ({exc}). Staying in LLM-only mode.")
                    self.use_rag = False
        if use_sensors  is not None: self.use_sensors  = use_sensors
        if use_behavior is not None: self.use_behavior = use_behavior
        self.chain = self._create_chain()

    def status(self) -> str:
        rag_label = (
            "RAG:on"             if (self.use_rag and self._rag is not None) else
            "RAG:off(unavail)"   if (self.use_rag and self._rag is None) else
            "RAG:off"
        )
        return (
            f"[{rag_label} | "
            f"sensors:{'on' if self.use_sensors else 'off'} | "
            f"behavior:{'on' if self.use_behavior else 'off'} | "
            f"model:{self.model_name}]"
        )

    def assess(
        self,
        sensors:    Optional["SensorData"]   = None,
        behavior:   Optional["BehaviorData"] = None,
        breed:      Optional[str] = None,
        horse_name: Optional[str] = None,
        horse_age:  Optional[int] = None,
        question:   str = "What is the potential health issue and what should I do?",
    ) -> "AssessmentResult":
        from app.services.horse_rag import (
            SensorData, BehaviorData, AssessmentResult,
            _format_sensors, _format_behavior,
            _parse_json_response, _parse_conditions,
            _parse_actions, _parse_monitoring, _estimate_confidence,
        )

        horse_id = horse_name or "Unknown Horse"
        if breed:      horse_id += f" ({breed})"
        if horse_age:  horse_id += f", age {horse_age} yrs"

        sections: List[str] = [f"## EQUINE HEALTH ASSESSMENT\n\n**Patient:** {horse_id}"]

        if self.use_sensors and sensors is not None:
            sections.append(f"### Sensor Readings\n{_format_sensors(sensors)}")

        if self.use_behavior and behavior is not None:
            sections.append(
                f"### Behavioural Observations (CV Pipeline Output)\n{_format_behavior(behavior)}"
            )

        docs:             list       = []
        sources:          List[str]  = []
        retrieval_time_s: float      = 0.0

        if self.use_rag and self._rag is not None:
            _q_sensors  = sensors  if (self.use_sensors  and sensors  is not None) else SensorData()
            _q_behavior = behavior if (self.use_behavior and behavior is not None) else BehaviorData()
            query = self._rag.build_query(_q_sensors, _q_behavior, breed=breed, horse_age=horse_age)

            _t0          = time.perf_counter()
            breed_filter = self._rag._build_breed_filter(breed)
            docs         = self._rag.retrieve(query, filter=breed_filter)
            retrieval_time_s = time.perf_counter() - _t0

            if docs:
                ctx = "\n\n---\n\n".join(
                    f"[Source: {d.metadata.get('source','?')} | "
                    f"Topic: {d.metadata.get('topic','general')}]\n{d.page_content}"
                    for d in docs
                )
                sections.append(f"### Retrieved Veterinary Knowledge\n{ctx}")
            sources = list({d.metadata.get("source", "unknown") for d in docs})

        sections.append(f"---\n\n**Clinical Question:** {question}")
        sections.append(
            'Respond with ONLY a valid JSON object — no markdown fences, no prose.\n'
            'Schema:\n'
            '{\n'
            '  "urgency": <integer 1-5>,\n'
            '  "possible_conditions": [<string>, ...],\n'
            '  "diagnosis_summary": "<string, ≤3 sentences>",\n'
            '  "immediate_actions": [<string>, ...],\n'
            '  "monitoring_tips": [<string>, ...],\n'
            '  "reasoning": "<string>"\n'
            '}\n'
            'urgency: 1=healthy, 2=monitor, 3=schedule vet, 4=urgent vet, 5=emergency.\n'
            'Base urgency only on the data provided — do not assume missing data is abnormal.'
        )

        prompt = "\n\n".join(sections)

        _t_llm       = time.perf_counter()
        raw_response = self.get_response(prompt, temperature=0.1)
        llm_time_s   = time.perf_counter() - _t_llm

        parsed      = _parse_json_response(raw_response)
        llm_urgency = max(1, min(5, int(parsed.get("urgency", 1))))

        return AssessmentResult(
            urgency=llm_urgency,
            call_vet=llm_urgency >= 4,
            possible_conditions=parsed.get("possible_conditions") or _parse_conditions(raw_response),
            diagnosis_summary=parsed.get("diagnosis_summary")    or raw_response[:600],
            immediate_actions=parsed.get("immediate_actions")    or _parse_actions(raw_response),
            monitoring_tips=parsed.get("monitoring_tips")        or _parse_monitoring(raw_response),
            confidence=_estimate_confidence(docs, llm_urgency),
            retrieved_sources=sources,
            raw_llm_response=raw_response,
            retrieval_time_s=retrieval_time_s,
            llm_time_s=llm_time_s,
        )

    def get_response(self, question: str, temperature: Optional[float] = None) -> str:
        if temperature is not None and temperature != self.default_temperature:
            tmp_model = ChatOllama(
                model=self.model_name, temperature=temperature,
                num_ctx=_DEFAULT_NUM_CTX, reasoning=False,
            )
            chain = self._build_prompt_template() | tmp_model | self.output_parser
            response = chain.invoke({"question": question, "history": self.history.messages})
        else:
            response = self.chain.invoke({"question": question, "history": self.history.messages})

        self.history.add_user_message(question)
        self.history.add_ai_message(response)
        return response

    def get_response_stream(self, question: str, temperature: Optional[float] = None):
        self.history.add_user_message(question)

        if temperature is not None and temperature != self.default_temperature:
            tmp_model = ChatOllama(
                model=self.model_name, temperature=temperature,
                num_ctx=_DEFAULT_NUM_CTX, reasoning=False,
            )
            chain = self._build_prompt_template() | tmp_model | self.output_parser
        else:
            chain = self.chain

        full_response = ""
        for chunk in chain.stream({"question": question, "history": self.history.messages[:-1]}):
            full_response += chunk
            yield chunk

        self.history.add_ai_message(full_response)

    def _rag_augment(self, question: str) -> str:
        if not (self.use_rag and self._rag is not None):
            return question
        try:
            docs = self._rag.retrieve(question)
            if docs:
                ctx = "\n\n".join(
                    f"[{d.metadata.get('source', '?')}] {d.page_content}"
                    for d in docs
                )
                return (
                    f"[Relevant veterinary context retrieved from knowledge base]\n"
                    f"{ctx}\n\n---\n\n{question}"
                )
        except Exception:
            pass
        return question

    def ask_stream(self, question: str):
        yield from self.get_response_stream(self._rag_augment(question))

    def ask(self, question: str, stream: bool = True) -> str:
        augmented = self._rag_augment(question)

        if stream:
            full_response = ""
            for chunk in self.get_response_stream(augmented):
                print(chunk, end="", flush=True)
                full_response += chunk
            print()
            return full_response
        else:
            return self.get_response(augmented)

    def clear_history(self) -> bool:
        self.history.clear()
        return len(self.history.messages) == 0

    def save_history(self, filepath: str) -> None:
        history_data = [
            {
                "type": msg.__class__.__name__,
                "content": msg.content,
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
            }
            for msg in self.history.messages
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"message_count": len(history_data), "messages": history_data},
                f, indent=2, ensure_ascii=False,
            )

    def load_history(self, filepath: str) -> bool:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.history.clear()
            for msg in data.get("messages", []):
                if msg["role"] == "user":
                    self.history.add_user_message(msg["content"])
                else:
                    self.history.add_ai_message(msg["content"])
            return True
        except Exception as e:
            print(f"[WARN] Failed to load history: {e}")
            return False

    def get_history_summary(self) -> Dict:
        messages = self.history.messages
        return {
            "total_messages": len(messages),
            "user_messages":  sum(1 for m in messages if isinstance(m, HumanMessage)),
            "ai_messages":    sum(1 for m in messages if isinstance(m, AIMessage)),
            "has_history":    len(messages) > 0,
        }

    def __repr__(self) -> str:
        s = self.get_history_summary()
        return f"HorseExpertAgent(model={self.model_name}, messages={s['total_messages']}, {self.status()})"
