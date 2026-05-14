"""
Service layer for Chatbot functionality.
Manages the HorseExpertAgent singleton and exposes mode-aware helpers.
"""
from pathlib import Path
from typing import Optional, Dict, List, Generator
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ChatbotService:
    """Singleton wrapper around HorseExpertAgent."""

    def __init__(self):
        self._agent = None
        self._history_file = Path(__file__).parent.parent.parent / "data" / "horse_conversation.json"
        self._history_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_agent(self):
        """Lazy-load the agent on first call."""
        if self._agent is None:
            try:
                from app.services.horse_expert_agent import HorseExpertAgent
                history_path = str(self._history_file) if self._history_file.exists() else None
                self._agent = HorseExpertAgent(
                    model_name=settings.DEFAULT_CHATBOT_MODEL_NAME,
                    history_file=history_path,
                    use_rag=True,
                    use_sensors=True,
                    use_behavior=True,
                )
                logger.info("HorseExpertAgent initialised (full mode)")
            except ImportError as e:
                logger.error(f"Failed to import HorseExpertAgent: {e}")
                raise ImportError(
                    "HorseExpertAgent not available. "
                    "Ensure langchain_ollama and RAG dependencies are installed."
                )
        return self._agent

    def set_mode(
        self,
        use_rag:      bool,
        use_sensors:  bool,
        use_behavior: bool,
    ) -> None:
        agent = self._get_agent()
        agent.set_mode(use_rag=use_rag, use_sensors=use_sensors, use_behavior=use_behavior)
        logger.info(f"Chatbot mode updated: {agent.status()}")

    def get_mode(self) -> Dict:
        agent = self._get_agent()
        return {
            "use_rag":      agent.use_rag,
            "use_sensors":  agent.use_sensors,
            "use_behavior": agent.use_behavior,
            "status":       agent.status(),
        }

    def _apply_mode_if_changed(
        self,
        use_rag:      bool,
        use_sensors:  bool,
        use_behavior: bool,
    ) -> None:
        agent = self._get_agent()
        if (agent.use_rag != use_rag
                or agent.use_sensors != use_sensors
                or agent.use_behavior != use_behavior):
            agent.set_mode(use_rag=use_rag, use_sensors=use_sensors, use_behavior=use_behavior)

    def get_response(
        self,
        question:     str,
        stream:       bool = False,
        use_rag:      bool = True,
        use_sensors:  bool = True,
        use_behavior: bool = True,
    ) -> str:
        agent = self._get_agent()
        self._apply_mode_if_changed(use_rag, use_sensors, use_behavior)
        response = agent.ask(question, stream=False)
        self._save_history()
        return response

    def get_response_stream(
        self,
        question: str,
    ) -> Generator[str, None, None]:
        agent = self._get_agent()
        for chunk in agent.ask_stream(question):
            yield chunk
        self._save_history()

    def get_response_stream_with_mode(
        self,
        question:     str,
        use_rag:      bool = True,
        use_sensors:  bool = True,
        use_behavior: bool = True,
    ) -> Generator[str, None, None]:
        agent = self._get_agent()
        self._apply_mode_if_changed(use_rag, use_sensors, use_behavior)
        for chunk in agent.ask_stream(question):
            yield chunk
        self._save_history()

    def get_history_summary(self) -> Dict:
        return self._get_agent().get_history_summary()

    def get_full_history(self) -> List[Dict]:
        agent = self._get_agent()
        return [
            {
                "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
                "content": msg.content,
            }
            for msg in agent.history.messages
        ]

    def clear_history(self) -> bool:
        agent = self._get_agent()
        success = agent.clear_history()
        if self._history_file.exists():
            self._history_file.unlink()
            logger.info(f"Deleted history file: {self._history_file}")
        return success

    def _save_history(self) -> None:
        try:
            self._get_agent().save_history(str(self._history_file))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def __repr__(self) -> str:
        if self._agent:
            return f"ChatbotService(agent={self._agent})"
        return "ChatbotService(agent=not_loaded)"
