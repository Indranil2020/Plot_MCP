import requests
import json
import os
from abc import ABC, abstractmethod
import google.generativeai as genai
from openai import OpenAI
from gallery_loader import get_gallery_prompt

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt, system_instruction=None):
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, model="llama3", api_url="http://localhost:11434/api/generate"):
        self.model = model
        self.api_url = api_url

    def generate(self, prompt, system_instruction=None):
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 2048
            }
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            return None

class GeminiProvider(LLMProvider):
    def __init__(self, api_key, model="gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(self, prompt, system_instruction=None):
        try:
            # Gemini handles system instructions differently, but for simplicity we'll prepend
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return None

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key, model="gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt, system_instruction=None):
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return None

class LLMService:
    def __init__(self):
        # Default to Ollama
        self.provider = OllamaProvider()

    def set_provider(self, provider_name, api_key=None, model_name=None):
        if provider_name.lower() == "gemini":
            if not api_key:
                raise ValueError("API Key required for Gemini")
            self.provider = GeminiProvider(api_key, model=model_name or "gemini-1.5-flash")
        elif provider_name.lower() == "openai":
            if not api_key:
                raise ValueError("API Key required for OpenAI")
            self.provider = OpenAIProvider(api_key, model=model_name or "gpt-4o")
        else:
            self.provider = OllamaProvider(model=model_name or "llama3")
        self.system_instruction = self._construct_system_instruction() # Update system instruction if provider changes

    async def process_query(self, query, context=None, current_code=None, history=None, data_analysis=None, url_analysis=None):
        """
        Process a query with intelligent context
        
        Args:
            query: User's question/request
            context: Data context (file path, preview)
            current_code: Previous plot code for iterative editing
            history: Conversation history
            data_analysis: Analysis of uploaded data structure
            url_analysis: Analysis of provided URLs/examples
        """
        prompt = self._construct_plot_prompt(query, context, current_code, history, data_analysis, url_analysis)
        
        try:
            response_text = self.provider.generate(prompt, self.system_instruction)
            code = self._extract_code(response_text)
            
            if code:
                return {
                    "type": "plot_code",
                    "code": code,
                    "text": "I've generated the plot code for you."
                }
            else:
                return {
                    "type": "text",
                    "text": response_text
                }
        except Exception as e:
            return {
                "type": "error",
                "text": f"Error processing query: {str(e)}"
            }

    def _construct_system_instruction(self):
        return """You are a Python data visualization expert using Matplotlib.
Your goal is to generate high-quality, publication-ready plots.
You must output valid Python code when requested.
"""

    def _construct_plot_prompt(self, query, context=None, current_code=None, history=None, data_analysis=None, url_analysis=None):
        prompt_parts = []
        
        prompt_parts.append("### Task")
        if current_code:
            prompt_parts.append("Edit the following existing code based on the user's request.")
        else:
            prompt_parts.append("Generate Python code to create a plot based on the user's request.")
        
        prompt_parts.append(f"\n### User Request\n{query}\n")

        has_data = data_analysis and data_analysis.get('columns')
        
        # Check if this is a gallery example request
        if any(phrase in query.lower() for phrase in ['example:', 'based on this example:', 'apply example:']):
            from gallery_loader import GalleryLoader
            loader = GalleryLoader()
            
            # Extract example title
            example_title = None
            for phrase in ['example:', 'based on this example:', 'apply example:']:
                if phrase in query.lower():
                    example_title = query.lower().split(phrase)[1].split('.')[0].strip()
                    break
            
            if example_title:
                # Search for the example
                examples = loader.search_examples(example_title, limit=1)
                if examples:
                    prompt_parts.append("\n### GALLERY EXAMPLE REQUEST:")
                    prompt_parts.append(f"The user wants to adapt this example: {examples[0]['title']}")
                    prompt_parts.append(f"\nExample code:\n```python\n{examples[0]['code']}\n```")
                    prompt_parts.append("\nYour task: Adapt this example to work with the user's data.")
                    if has_data:
                        prompt_parts.append("IMPORTANT: Replace the example's data with the actual data from the uploaded file.")
                        prompt_parts.append("Use the column names from the data analysis below.")
        
        # Add data analysis context
        if has_data:
            prompt_parts.append("\n### Data Structure")
            prompt_parts.append(f"Shape: {data_analysis.get('shape', 'unknown')}")
            prompt_parts.append(f"Columns: {', '.join(data_analysis.get('columns', []))}")
            prompt_parts.append(f"Numeric columns: {', '.join(data_analysis.get('numeric_cols', []))}")
            prompt_parts.append(f"Categorical columns: {', '.join(data_analysis.get('categorical_cols', []))}")
            
            if data_analysis.get('suggested_plots'):
                prompt_parts.append("\n### Suggested Plot Types (based on data structure):")
                for suggestion in data_analysis['suggested_plots'][:3]:
                    prompt_parts.append(f"- {suggestion['type']}: {suggestion['reason']}")
            
            if data_analysis.get('warnings'):
                prompt_parts.append("\n### Data Warnings:")
                for warning in data_analysis['warnings']:
                    prompt_parts.append(f"- {warning}")
        
        # Add URL analysis context
        if url_analysis:
            prompt_parts.append("\n### User Provided Example")
            prompt_parts.append(f"Type: {url_analysis.get('type', 'unknown')}")
            prompt_parts.append(f"Description: {url_analysis.get('description', 'N/A')}")
            if url_analysis.get('suggestion'):
                prompt_parts.append(f"Guidance: {url_analysis['suggestion']}")
        
        if context:
            prompt_parts.append(f"\n### Data Context\n{context}\n")
        
        if current_code:
            prompt_parts.append(f"\n### Current Plot Code (for editing)\n```python\n{current_code}\n```\n")

        if history:
            prompt_parts.append(f"\n### Conversation History\n{history}\n")

        prompt_parts.append("\n### Instructions")
        prompt_parts.append("1. Use 'matplotlib.pyplot' as 'plt'. Seaborn ('sns') is also available.")

        if has_data:
            prompt_parts.append("2. Assume 'df' is already loaded with the data. Use the columns provided in the 'Data Structure' section.")
        else:
            prompt_parts.append("2. **IMPORTANT**: No data file has been provided. Do NOT use a variable named 'df'. If the user's request requires data (e.g. plotting from a file), you MUST ask them to upload a file. If the request is for a general plot that does not require user data (e.g. 'plot a sine wave'), you can generate the data yourself using `numpy`.")
        
        prompt_parts.append("""3. **Publication Quality**:
    - Use a professional style (e.g., `plt.style.use('seaborn-v0_8-whitegrid')` or `sns.set_style()`).
    - Ensure fonts are readable.
    - Add clear titles, labels, and legends.
    - Use high-contrast, colorblind-friendly colors where possible.
4. **Code Requirements**:
    - Generate ONLY the Python code inside markdown code blocks.
    - Do NOT use `plt.show()`.
    - Handle potential NaN values.
    - **IMPORTANT**: When using categorical data for colors (e.g., `c=` in scatter), use `pd.Categorical(df['column']).codes` or map to numeric values.
5. **Editing Existing Plots**:
    - When the user asks to change a specific element (title, xlabel, ylabel, legend, colors, etc.), modify ONLY that element.
    - Keep all other aspects of the plot unchanged unless explicitly requested.
    - If the user says "change the title to X", only modify `plt.title()` or `ax.set_title()`.
    - If the user says "change the x-axis label to Y", only modify `plt.xlabel()` or `ax.set_xlabel()`.
    - If the user says "change the y-axis label to Z", only modify `plt.ylabel()` or `ax.set_ylabel()`.
    - If the user says "move legend to upper left", only modify the legend location parameter.
    - DO NOT change the data being plotted unless explicitly asked.
6. **Matplotlib Capabilities**:
    - You can use ANY Matplotlib feature (subplots, 3D, animations, etc.) if appropriate.
""")
        
        # Add official Matplotlib gallery reference (509 examples)
        prompt_parts.append(get_gallery_prompt())
        
        return '\n'.join(prompt_parts)

    def _extract_code(self, text):
        if "```python" in text:
            code = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            # Extract code from generic code block
            parts = text.split("```")
            if len(parts) >= 3:
                code = parts[1]
                # Remove language identifier if present (e.g., "markdown\n")
                if '\n' in code:
                    first_line = code.split('\n')[0].strip()
                    # If first line is a language identifier, skip it
                    if first_line and not any(c in first_line for c in [' ', '(', '=', '#']):
                        code = '\n'.join(code.split('\n')[1:])
            else:
                return None
        else:
            # If no code block, maybe the whole text is code? 
            # But usually LLMs chat a bit. Let's be strict for now.
            return None
        
        code = code.strip()
        lines = code.split('\n')
        # Filter out common non-code lines and plt.show()
        filtered_lines = []
        for line in lines:
            if line.lower().startswith('here is'):
                continue
            if 'plt.show()' in line:
                continue
            filtered_lines.append(line)
        return '\n'.join(filtered_lines)
