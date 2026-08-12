import re
import json
import ollama
from typing import Optional, Dict, Any

class BaseAgent:
    def __init__(self, agent_name: str = "BaseAgent", model_used: str = "qwen3:8b"):
        """
        Neengatha model mathanum na, inga 'qwen3:8b' nu irukka sthalathula mathikonga.
        Example: 'llama3.1:8b' or 'gemma2:9b'.
        """
        self.agent_name = agent_name
        self.model_used = model_used
        self.model_name = model_used

    def _clean_json(self, raw_output: str) -> Dict[str, Any]:
        """
        Ollama la irundhu vandha response la irukka extra words ah cut panni,
        Pure JSON ah eduthu Python Dictionary ah mathi kudukum.
        """
        # 1. Markdown (```json ... ```) ah remove pannu
        cleaned = re.sub(r'```json\s*', '', raw_output)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        # 2. JSON object { ... } or array [ ... ] ah extract pannu
        match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
        if not match:
            # JSON eh illa na error pottu vidu
            raise ValueError(f"No JSON found in response: {raw_output[:100]}")
        
        json_str = match.group(1)
        
        # 3. Trailing commas ( , } or , ] ) ah fix pannu (Gemma/Qwen sometimes potu vidum)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 4. Parse panni return pannu
        return json.loads(json_str)

    def call_llm(self, prompt: str, json_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Idhu dhan unga 'Start Button' (Washing machine button).
        Nee inga prompt ah kudutha, idhu Ollama ku anuppum, response ah clean panni
        Dictionary ah return pannum.
        """
        # System prompt - JSON mattum kudu nu kattayam sollu
        system_prompt = "You are a forensic AI expert. You MUST respond ONLY with valid JSON. Do not include any explanations, greetings, or markdown formatting."
        
        full_prompt = f"{system_prompt}\n\nTask: {prompt}"
        
        # JSON schema kuduthiruntha, adhaiyum prompt la force pannu
        if json_schema:
            full_prompt += f"\n\nYou MUST output JSON matching this exact structure: {json.dumps(json_schema)}"

        # Ollama call pannu
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": full_prompt}],
            options={
                "temperature": 0.0,      # Zero randomness = Strict output
                "num_predict": 2048,     # Max tokens
                "top_k": 10,
                "top_p": 0.9,
                "num_ctx": 8192          # 8k context window (unga RAM/VRAM ku set)
            }
        )
        
        raw_text = response['message']['content']
        
        # Clean panni return pannu
        return self._clean_json(raw_text)