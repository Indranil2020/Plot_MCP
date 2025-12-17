# System Architecture

## Overview

The Plot MCP system consists of a Python FastAPI backend and a React frontend. The backend handles data processing, LLM interaction, and plot generation, while the frontend provides the user interface.

## System Diagram

```mermaid
graph TD
    User[User] --> Frontend[React Frontend]
    Frontend -->|HTTP Requests| Backend[FastAPI Backend]
    
    subgraph Backend Services
        Backend --> LLM[LLM Service]
        Backend --> Plot[Plot Engine]
        Backend --> Data[Data Manager]
        Backend --> Gallery[Gallery Loader]
    end
    
    subgraph External
        LLM -->|API Call| Ollama[Ollama / Local LLM]
        LLM -->|API Call| Cloud[OpenAI / Gemini]
        Plot -->|Execute| Matplotlib[Matplotlib Library]
    end
```

## Component Details

### 1. Data Manager
Handles file uploads and parsing. It intelligently detects format delimiters (CSV, TSV, space) and creates a Pandas DataFrame. It generates data summaries for the LLM.

### 2. LLM Service
Constructs prompts for the Large Language Model. It injects data context, conversation history, and instructions. It parses the LLM response to extract executable Python code.

### 3. Plot Engine
safe execution environment for generated Python code. It applies publication-quality styles (fonts, formatting) and renders the plot to an image buffer. It also extracts interaction metadata (bounding boxes for titles/labels).

### 4. Frontend
A React application that manages state (chat history, data). It renders the plot image and handles interactive clicks by mapping coordinates to the metadata provided by the Plot Engine.

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant L as LLM
    participant P as Plot Engine

    U->>F: Upload Data / Paste Text
    F->>B: /paste_data
    B-->>F: Data Analysis & Preview

    U->>F: "Plot X vs Y"
    F->>B: /chat context
    B->>L: Generate Python Code
    L-->>B: Code
    
    B->>P: Execute Code
    P-->>B: Image + Metadata
    B-->>F: Response + Image
    F-->>U: Display Plot
```
