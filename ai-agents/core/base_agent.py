"""
core/base_agent.py

Common base class for all INVESTCOPS AI agents.

All LLM-based agents use:

Agent
    ↓
BaseAgent
    ↓
Ollama
    ↓
Qwen3:8b

Features:
- Automatic retry (3 attempts) with exponential backoff
- JSON cleaning (removes markdown, trailing commas, extracts JSON)
- Required key validation
- Debug logging (prints raw Qwen response)
- Increased context window (8192 tokens)
"""

import json
import re
import time
from typing import Optional, Dict, Any

import ollama


class BaseAgent:
    """
    Common base class for all INVESTCOPS AI agents.

    Handles:
    - Agent identification
    - Ollama communication
    - JSON parsing
    - Retry logic
    - Basic response validation
    """

    def __init__(
        self,
        agent_name: str,
        model_name: str = "qwen3:8b",
    ):
        """
        Initialize the base agent.
        """
        self.agent_name = agent_name
        self.model_name = model_name
        self.max_retries = 3  # Number of retry attempts

    # ============================================================
    # LLM CALL
    # ============================================================

    def call_llm(
        self,
        prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a prompt to Ollama and return parsed JSON.

        Features:
        - Retries up to 3 times on failure
        - Exponential backoff (1s, 2s, 4s)
        - Removes markdown and <think> tags
        - Parses and cleans JSON
        """

        system_prompt = (
            "You are a forensic AI assistant for INVESTCOPS AI. "
            "Analyze only the information provided in the task. "
            "Do NOT invent evidence, people, locations, timestamps, "
            "relationships, or conclusions. "
            "Do NOT output <think> tags, markdown, code fences, "
            "or any explanatory text. "
            "Return ONLY valid JSON."
        )

        full_prompt = (
            f"{system_prompt}\n\n"
            f"TASK:\n{prompt}"
        )

        # Add expected JSON structure
        if json_schema:
            full_prompt += (
                "\n\nReturn JSON matching this structure:\n"
                + json.dumps(json_schema, indent=2)
            )

        # Retry loop
        last_exception = None

        for attempt in range(1, self.max_retries + 1):

            try:
                print(
                    f"   🔄 {self.agent_name}: "
                    f"LLM call attempt {attempt}/{self.max_retries}..."
                )

                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt,
                        }
                    ],
                    options={
                        "temperature": 0.0,
                        "num_predict": 1024,
                        "top_k": 10,
                        "top_p": 0.9,
                        "num_ctx": 8192,  # 👈 INCREASED from 4096 to 8192
                    },
                )

                # ----------------------------------------------------
                # Extract response text
                # ----------------------------------------------------

                raw_text = response["message"]["content"]

                if not raw_text or not raw_text.strip():
                    raise ValueError("Ollama returned an empty response.")

                # ----------------------------------------------------
                # Debug print
                # ----------------------------------------------------

                print("\n========== RAW QWEN RESPONSE ==========")
                print(raw_text[:500] + ("..." if len(raw_text) > 500 else ""))
                print("========== END RAW RESPONSE ==========\n")

                # ----------------------------------------------------
                # Clean and parse JSON
                # ----------------------------------------------------

                parsed = self._clean_json(raw_text)

                print(f"   ✅ {self.agent_name}: Success! (Attempt {attempt})")

                return parsed

            except Exception as exc:
                last_exception = exc
                print(f"   ❌ {self.agent_name}: Attempt {attempt} failed: {exc}")

                # If this was the last attempt, don't wait
                if attempt == self.max_retries:
                    break

                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** (attempt - 1)
                print(f"   ⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        # If we get here, all retries failed
        raise RuntimeError(
            f"{self.agent_name}: All {self.max_retries} LLM attempts failed. "
            f"Last error: {last_exception}. "
            "Check that Ollama is running and model 'qwen3:8b' is available."
        ) from last_exception

    # ============================================================
    # JSON CLEANING
    # ============================================================

    @staticmethod
    def _clean_json(
        raw_output: str,
    ) -> Dict[str, Any]:
        """
        Convert Qwen's response into a Python dictionary.

        Handles:
        1. Strips whitespace
        2. Removes markdown code fences (```json ... ```)
        3. Removes <think>...</think> tags
        4. Extracts the first JSON object { ... }
        5. Fixes trailing commas
        6. Validates JSON structure
        """

        if not raw_output or not raw_output.strip():
            raise ValueError("LLM returned an empty response.")

        cleaned = raw_output.strip()

        # ------------------------------------------------------------
        # Remove <think> tags (Qwen3 reasoning tokens)
        # ------------------------------------------------------------

        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # ------------------------------------------------------------
        # Remove markdown code fences
        # ------------------------------------------------------------

        cleaned = re.sub(
            r"```json\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"```\s*",
            "",
            cleaned,
        )

        cleaned = cleaned.strip()

        # ------------------------------------------------------------
        # Try direct JSON parsing first (fast path)
        # ------------------------------------------------------------

        try:
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError(
                    "Expected JSON object but received "
                    f"{type(parsed).__name__}."
                )
            return parsed
        except json.JSONDecodeError:
            pass

        # ------------------------------------------------------------
        # Find JSON object inside surrounding text
        # ------------------------------------------------------------

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                "No valid JSON object found in LLM response. "
                f"Response preview: {raw_output[:300]}"
            )

        json_text = cleaned[start:end + 1]

        # ------------------------------------------------------------
        # Remove trailing commas (common LLM error)
        # ------------------------------------------------------------

        json_text = re.sub(
            r",\s*}",
            "}",
            json_text,
        )

        json_text = re.sub(
            r",\s*]",
            "]",
            json_text,
        )

        # ------------------------------------------------------------
        # Parse extracted JSON
        # ------------------------------------------------------------

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned malformed JSON. "
                f"Response preview: {raw_output[:500]}"
            ) from exc

        if not isinstance(parsed, dict):
            raise ValueError(
                f"Expected a JSON object, got {type(parsed).__name__}."
            )

        return parsed

    # ============================================================
    # VALIDATE REQUIRED KEYS
    # ============================================================

    @staticmethod
    def validate_required_keys(
        data: Dict[str, Any],
        required_keys: list[str],
    ) -> None:
        """
        Verify that required keys exist in the LLM response.

        Raises ValueError if any key is missing.
        """

        missing = [
            key
            for key in required_keys
            if key not in data
        ]

        if missing:
            raise ValueError(
                "LLM response is missing required keys: "
                + ", ".join(missing)
            )