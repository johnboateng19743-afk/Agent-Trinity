"""
Trinity Orchestrator — Intent Router.
Classifies user intent and routes to the appropriate skill.
"""

import re
import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger(__name__)


@dataclass
class Intent:
    """Classified intent with skill routing info."""
    skill: str
    action: str
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str = ""


class IntentRouter:
    """Routes user commands to appropriate skills based on intent classification."""

    # Intent patterns for fast regex-based routing
    INTENT_PATTERNS = {
        "filesystem.read": [
            r"(?i)(read|show|display|open|view|what's in|what is in)\s+.*(file|document|folder|dir)",
            r"(?i)what('s| is) (in|on) my",
        ],
        "filesystem.search": [
            r"(?i)(find|search|locate|look for)\s+",
            r"(?i)(where is|where are|where's)\s+",
        ],
        "filesystem.write": [
            r"(?i)(create|make|write|new)\s+.*(file|document|folder|note)",
        ],
        "filesystem.edit": [
            r"(?i)(edit|modify|change|update|set|rename)\s+",
        ],
        "filesystem.move": [
            r"(?i)(move|transfer|relocate)\s+",
        ],
        "filesystem.delete": [
            r"(?i)(delete|remove|trash|erase|get rid of)\s+",
        ],
        "calendar": [
            r"(?i)(calendar|schedule|meeting|event|appointment)\s+",
            r"(?i)(what('s| is) on my calendar|what do i have)\s+",
            r"(?i)(when am i free|when is my next)\s+",
        ],
        "email": [
            r"(?i)(email|mail|inbox|send|reply|read my)\s+",
            r"(?i)(unread|new email|messages?)\s+",
        ],
        "drive": [
            r"(?i)(google drive|drive|upload|download from cloud)\s+",
            r"(?i)(share this|share the)\s+",
        ],
        "maps.location": [
            r"(?i)(where am i|my location|where('s| is) the nearest)\s+",
            r"(?i)(nearby|around me|close to me)\s+",
        ],
        "maps.directions": [
            r"(?i)(directions|navigate|how (do i|to) get|route to|drive to)\s+",
            r"(?i)(how far|how long|distance|eta)\s+",
        ],
    }

    def __init__(self, config: dict):
        self.config = config
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict[str, list[re.Pattern]]:
        """Pre-compile regex patterns for faster matching."""
        compiled = {}
        for skill, patterns in self.INTENT_PATTERNS.items():
            compiled[skill] = [re.compile(p) for p in patterns]
        return compiled

    async def classify(self, text: str, context: dict | None = None) -> Intent:
        """Classify user intent from text input."""
        text = text.strip()

        # Step 1: Try fast regex matching
        regex_intent = self._regex_classify(text)
        if regex_intent and regex_intent.confidence >= 0.8:
            logger.info("router.classified", method="regex", skill=regex_intent.skill)
            return regex_intent

        # Step 2: Use LLM for classification (cloud)
        if regex_intent and regex_intent.confidence >= 0.5:
            logger.info("router.classified", method="regex_low_conf", skill=regex_intent.skill)
            return regex_intent

        # Step 3: Default to LLM conversation
        logger.info("router.unclassified", fallback="llm_conversation")
        return Intent(
            skill="llm_conversation",
            action="chat",
            entities={"text": text},
            confidence=0.3,
            raw_text=text,
        )

    def _regex_classify(self, text: str) -> Intent | None:
        """Classify intent using regex pattern matching."""
        best_match = None
        best_confidence = 0.0

        for skill, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    confidence = 0.7 + (0.1 * len(match.group()) / max(len(text), 1))
                    confidence = min(confidence, 0.95)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = Intent(
                            skill=skill,
                            action=self._extract_action(skill, text),
                            entities=self._extract_entities(text, skill),
                            confidence=best_confidence,
                            raw_text=text,
                        )

        return best_match

    def _extract_action(self, skill: str, text: str) -> str:
        """Extract the specific action from text."""
        action_patterns = {
            "filesystem.read": r"(?i)(read|show|display|open|view)",
            "filesystem.search": r"(?i)(find|search|locate|look for)",
            "filesystem.write": r"(?i)(create|make|write|new)",
            "filesystem.edit": r"(?i)(edit|modify|change|update|set|rename)",
            "filesystem.move": r"(?i)(move|transfer|copy)",
            "filesystem.delete": r"(?i)(delete|remove|trash)",
            "calendar": r"(?i)(schedule|create|cancel|move|view)",
            "email": r"(?i)(read|send|reply|delete|search)",
        }
        patterns = action_patterns.get(skill, [])
        if isinstance(patterns, str):
            patterns = [patterns]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).lower()
        return "execute"

    def _extract_entities(self, text: str, skill: str) -> dict:
        """Extract named entities from the text."""
        entities = {"raw_text": text}

        # Extract file paths
        path_match = re.search(r"(?i)(?:in|from|to|at)\s+([A-Z]:\\[\w\\]+|~?/[\w/.]+|[\w.]+\.\w+)", text)
        if path_match:
            entities["path"] = path_match.group(1)

        # Extract times
        time_match = re.search(r"(?i)(\d{1,2}:\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm))", text)
        if time_match:
            entities["time"] = time_match.group(1)

        # Extract dates
        date_match = re.search(r"(?i)(tomorrow|today|next\s+\w+|on\s+\w+|this\s+\w+)", text)
        if date_match:
            entities["date"] = date_match.group(1)

        return entities
