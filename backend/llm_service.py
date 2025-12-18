"""LLM service orchestration for plotting requests."""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import google.generativeai as genai
import requests
from openai import OpenAI

from gallery_loader import get_gallery_prompt


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a response for the given prompt."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Ollama provider wrapper."""

    def __init__(
        self, model: str = "llama3", api_url: str = "http://localhost:11434/api/generate"
    ) -> None:
        self.model = model
        self.api_url = api_url

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 2048},
        }

        response = requests.post(self.api_url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")


class GeminiProvider(LLMProvider):
    """Google Gemini provider wrapper."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        response = self.model.generate_content(full_prompt)
        return response.text


class OpenAIProvider(LLMProvider):
    """OpenAI provider wrapper."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=0.2
        )
        return response.choices[0].message.content


class LLMService:
    """Service wrapper that prepares prompts and parses LLM output."""

    def __init__(self) -> None:
        default_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.provider: LLMProvider = OllamaProvider(model=default_model)
        self.system_instruction = self._construct_system_instruction()
        self.logger = self._setup_logger()

    def set_provider(
        self, provider_name: str, api_key: Optional[str] = None, model_name: Optional[str] = None
    ) -> None:
        if provider_name.lower() == "gemini":
            if not api_key:
                raise ValueError("API Key required for Gemini")
            self.provider = GeminiProvider(api_key, model=model_name or "gemini-1.5-flash")
        elif provider_name.lower() == "openai":
            if not api_key:
                raise ValueError("API Key required for OpenAI")
            self.provider = OpenAIProvider(api_key, model=model_name or "gpt-4o")
        else:
            default_model = os.getenv("OLLAMA_MODEL", "llama3")
            self.provider = OllamaProvider(model=model_name or default_model)
        self.system_instruction = self._construct_system_instruction()

    async def process_query(
        self,
        query: str,
        context: Optional[str] = None,
        current_code: Optional[str] = None,
        history: Optional[str] = None,
        data_analysis: Optional[Dict[str, object]] = None,
        url_analysis: Optional[Dict[str, object]] = None,
        file_catalog: Optional[List[Dict[str, object]]] = None,
    ) -> Dict[str, object]:
        """Process a user query with structured context."""
        clarification = self._needs_clarification(query, file_catalog, history)
        if clarification:
            return {"type": "clarify", "text": clarification}

        prompt = self._construct_plot_prompt(
            query,
            context=context,
            current_code=current_code,
            history=history,
            data_analysis=data_analysis,
            url_analysis=url_analysis,
            file_catalog=file_catalog,
        )

        response_text = self.provider.generate(prompt, self.system_instruction)
        self.logger.info("prompt=%s", prompt)
        self.logger.info("response=%s", response_text)
        code = self._extract_code(response_text)

        if code:
            return {
                "type": "plot_code",
                "code": code,
                "text": "I have generated the plot code for you.",
            }

        return {"type": "text", "text": response_text}

    def _construct_system_instruction(self) -> str:
        return (
            "You are a friendly data visualization expert using Python and Matplotlib.\n"
            "Your goal is to assist the user in creating high-quality, publication-ready plots, "
            "and to chat naturally.\n"
            "If the user greets you, respond naturally without generating code.\n"
            "If the user asks for a plot, output valid Python code inside markdown code blocks."
        )

    def _setup_logger(self) -> logging.Logger:
        log_dir = os.path.join("backend", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logger = logging.getLogger("llm_service")
        if logger.handlers:
            return logger
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(os.path.join(log_dir, "llm.log"))
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _needs_clarification(
        self,
        query: str,
        file_catalog: Optional[List[Dict[str, object]]],
        history: Optional[str],
    ) -> Optional[str]:
        normalized = query.lower().strip()
        if not normalized:
            return "What would you like to plot?"

        if self._is_followup_reply(normalized, history):
            return None

        plot_keywords = {
            "plot",
            "scatter",
            "line",
            "bar",
            "hist",
            "histogram",
            "box",
            "boxplot",
            "heatmap",
            "violin",
            "density",
            "curve",
            "trend",
            "time series",
        }

        if normalized in {"hi", "hello", "hey"} or normalized.startswith("hi "):
            return None

        if file_catalog and len(file_catalog) > 1:
            aliases = [entry.get("alias", "") for entry in file_catalog]
            filenames = [entry.get("filename", "") for entry in file_catalog]
            mentions_alias = any(alias and alias in normalized for alias in aliases)
            mentions_file = any(name and name.lower() in normalized for name in filenames)
            mentions_join = any(token in normalized for token in ["join", "merge", "combine"])
            if not mentions_alias and not mentions_file and not mentions_join:
                return (
                    "You selected multiple files. Which files should I use, and how should they be joined "
                    "(e.g., merge on a shared column or overlay as separate series)?"
                )

        if not any(keyword in normalized for keyword in plot_keywords):
            return "What kind of visualization would you like me to create?"

        return None

    def _is_followup_reply(self, normalized: str, history: Optional[str]) -> bool:
        if not history:
            return False

        short_replies = {
            "2d",
            "3d",
            "2-d",
            "3-d",
            "yes",
            "no",
            "ok",
            "okay",
            "sure",
            "line",
            "scatter",
            "bar",
            "hist",
            "histogram",
        }

        if normalized in short_replies:
            return True

        if len(normalized) <= 6:
            return True

        last_line = history.strip().splitlines()[-1].strip() if history.strip() else ""
        if last_line.lower().startswith("assistant:") and last_line.endswith("?"):
            return True

        return False

    def _construct_plot_prompt(
        self,
        query: str,
        context: Optional[str] = None,
        current_code: Optional[str] = None,
        history: Optional[str] = None,
        data_analysis: Optional[Dict[str, object]] = None,
        url_analysis: Optional[Dict[str, object]] = None,
        file_catalog: Optional[List[Dict[str, object]]] = None,
    ) -> str:
        prompt_parts: List[str] = []

        prompt_parts.append("### Task")
        if current_code:
            prompt_parts.append(
                "Edit the existing code below if the user requested a change. "
                "If they are just chatting, ignore the code."
            )
        else:
            prompt_parts.append(
                "If the user wants a plot, generate Python code. "
                "If the user is just chatting or asking for explanation, just answer them."
            )

        prompt_parts.append(f"\n### User Request\n{query}\n")

        has_single_data = bool(data_analysis and data_analysis.get("columns"))

        if any(
            phrase in query.lower()
            for phrase in ["example:", "based on this example:", "apply example:"]
        ):
            from gallery_loader import GalleryLoader

            loader = GalleryLoader()
            example_title = None
            for phrase in ["example:", "based on this example:", "apply example:"]:
                if phrase in query.lower():
                    example_title = query.lower().split(phrase)[1].split(".")[0].strip()
                    break

            if example_title:
                examples = loader.search_examples(example_title, limit=1)
                if examples:
                    prompt_parts.append("\n### GALLERY EXAMPLE REQUEST:")
                    prompt_parts.append(
                        f"The user wants to adapt this example: {examples[0]['title']}"
                    )
                    prompt_parts.append(
                        f"\nExample code:\n```python\n{examples[0]['code']}\n```"
                    )
                    prompt_parts.append(
                        "\nYour task: Adapt this example to work with the user's data."
                    )
                    if has_single_data or file_catalog:
                        prompt_parts.append(
                            "IMPORTANT: Replace the example's data with the actual data "
                            "from the uploaded file(s)."
                        )

        if file_catalog:
            alias_map = {entry.get("alias", ""): entry.get("filename", "") for entry in file_catalog}
            prompt_parts.append("\n### Selected Files")
            for entry in file_catalog:
                alias = entry.get("alias", "")
                filename = entry.get("filename", "")
                analysis = entry.get("analysis", {})
                prompt_parts.append(f"- {alias} (source: {filename})")
                prompt_parts.append(
                    f"  Shape: {analysis.get('shape', 'unknown')}"
                )
                prompt_parts.append(
                    f"  Columns: {', '.join(analysis.get('columns', []))}"
                )
                prompt_parts.append(
                    f"  Numeric columns: {', '.join(analysis.get('numeric_cols', []))}"
                )
                prompt_parts.append(
                    "  Categorical columns: "
                    f"{', '.join(analysis.get('categorical_cols', []))}"
                )
            prompt_parts.append("\n### Dataset Alias Map")
            prompt_parts.append(json.dumps(alias_map, indent=2))

        if has_single_data:
            prompt_parts.append("\n### Data Structure")
            prompt_parts.append(f"Shape: {data_analysis.get('shape', 'unknown')}")
            prompt_parts.append(
                f"Columns: {', '.join(data_analysis.get('columns', []))}"
            )
            prompt_parts.append(
                f"Numeric columns: {', '.join(data_analysis.get('numeric_cols', []))}"
            )
            prompt_parts.append(
                f"Categorical columns: {', '.join(data_analysis.get('categorical_cols', []))}"
            )

            if data_analysis.get("suggested_plots"):
                prompt_parts.append("\n### Suggested Plot Types (based on data structure):")
                for suggestion in data_analysis["suggested_plots"][:3]:
                    prompt_parts.append(
                        f"- {suggestion['type']}: {suggestion['reason']}"
                    )

            if data_analysis.get("warnings"):
                prompt_parts.append("\n### Data Warnings:")
                for warning in data_analysis["warnings"]:
                    prompt_parts.append(f"- {warning}")

        if url_analysis:
            prompt_parts.append("\n### User Provided Example")
            prompt_parts.append(f"Type: {url_analysis.get('type', 'unknown')}")
            prompt_parts.append(
                f"Description: {url_analysis.get('description', 'N/A')}"
            )
            if url_analysis.get("suggestion"):
                prompt_parts.append(f"Guidance: {url_analysis['suggestion']}")

        if context:
            prompt_parts.append(f"\n### Data Context\n{context}\n")

        if current_code:
            prompt_parts.append(
                f"\n### Current Plot Code (for editing)\n```python\n{current_code}\n```\n"
            )

        if history:
            prompt_parts.append(f"\n### Conversation History\n{history}\n")

        prompt_parts.append("\n### Instructions")
        prompt_parts.append("1. Use 'matplotlib.pyplot' as 'plt'. Seaborn ('sns') is also available.")
        prompt_parts.append("   Do NOT import modules; use the provided `plt`, `pd`, `np`, and `sns` objects.")
        prompt_parts.append("   Do NOT load data from files; use the provided dataframes only.")

        if file_catalog:
            prompt_parts.append(
                "2. Multiple datasets are preloaded. Use `dfs['alias']` to access them."
            )
            prompt_parts.append(
                "   Each alias is also available as a variable (for example, `df_sales`)."
            )
            prompt_parts.append("   The variable `df` refers to the first selected file.")
        elif has_single_data:
            prompt_parts.append(
                "2. Assume 'df' is already loaded with the data. "
                "Use the columns provided in the 'Data Structure' section."
            )
        else:
            prompt_parts.append(
                "2. IMPORTANT: No data file has been provided. Do NOT use a variable named 'df'. "
                "If the user's request requires data, ask them to upload a file. "
                "If the request is for a general plot, generate synthetic data with numpy."
            )

        prompt_parts.append(
            """3. Publication Quality:
    - Use a professional style (e.g., `plt.style.use('seaborn-v0_8-whitegrid')` or `sns.set_style()`).
    - Ensure fonts are readable.
    - Add clear titles, labels, and legends.
    - Use high-contrast, colorblind-friendly colors where possible.
4. Code Requirements:
    - Generate ONLY the Python code inside markdown code blocks.
    - Do NOT use `plt.show()`.
    - Handle potential NaN values.
    - When using categorical data for colors (e.g., `c=` in scatter), use `pd.Categorical(df['column']).codes`.
5. Editing Existing Plots:
    - When the user asks to change a specific element (title, xlabel, ylabel, legend, colors, etc.), modify ONLY that element.
    - Keep all other aspects of the plot unchanged unless explicitly requested.
    - If the user says "change the title to X", only modify `plt.title()` or `ax.set_title()`.
    - If the user says "change the x-axis label to Y", only modify `plt.xlabel()` or `ax.set_xlabel()`.
    - If the user says "change the y-axis label to Z", only modify `plt.ylabel()` or `ax.set_ylabel()`.
    - If the user says "move legend to upper left", only modify the legend location parameter.
    - Do NOT change the data being plotted unless explicitly asked.
6. Matplotlib Capabilities:
    - You can use ANY Matplotlib feature (subplots, 3D, animations, etc.) if appropriate.
"""
        )

        prompt_parts.append(get_gallery_prompt())
        return "\n".join(prompt_parts)

    def _extract_code(self, text: str) -> Optional[str]:
        if "```python" in text:
            code = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                code = parts[1]
                if "\n" in code:
                    first_line = code.split("\n")[0].strip()
                    if first_line and not any(c in first_line for c in [" ", "(", "=", "#"]):
                        code = "\n".join(code.split("\n")[1:])
            else:
                return None
        else:
            return None

        code = code.strip()
        lines = code.split("\n")
        filtered_lines = []
        for line in lines:
            if line.lower().startswith("here is"):
                continue
            if "plt.show()" in line:
                continue
            filtered_lines.append(line)
        return "\n".join(filtered_lines)
