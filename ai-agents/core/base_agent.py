import re
import json
import ollama
from typing import Optional, Dict, Any

class BaseAgent:
    def __init__(self, agent_name: str = "BaseAgent", model_used: str = "qwen3:8b"):
        """
        Base Agent class that all agents inherit from
        
        Args:
            agent_name: Name of the agent
            model_used: Ollama model to use (default: qwen3:8b)
        """
        self.agent_name = agent_name
        self.model_used = model_used
        self.use_llm = False  # DISABLE LLM - Using regex extraction instead

    def _clean_json(self, raw_output: str) -> Dict[str, Any]:
        """Clean JSON from Ollama response"""
        cleaned = re.sub(r'`json\s*', '', raw_output)
        cleaned = re.sub(r'`\s*', '', cleaned)
        match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response: {raw_output[:100]}")
        json_str = match.group(1)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        return json.loads(json_str)

    def call_llm(self, prompt: str, json_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Call LLM - SKIPPED because use_llm is False"""
        if not self.use_llm:
            return {}

        system_prompt = "You are a forensic AI expert. You MUST respond ONLY with valid JSON."
        full_prompt = f"{system_prompt}\n\nTask: {prompt}"
        
        if json_schema:
            full_prompt += f"\n\nYou MUST output JSON matching this structure: {json.dumps(json_schema)}"

        try:
            response = ollama.chat(
                model=self.model_used,
                messages=[{"role": "user", "content": full_prompt}],
                options={"temperature": 0.0, "num_predict": 2048}
            )
            raw_text = response['message']['content']
            return self._clean_json(raw_text)
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return {}
