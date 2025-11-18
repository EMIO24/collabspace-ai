from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# 1. AI Usage Model
# ----------------------------------------------------------------------

class AIUsage(BaseModel):
    """
    Model for tracking API usage, token counts, and estimated costs across all providers.
    
    The 'provider' field is crucial for distinguishing between OpenAI, Anthropic, and Gemini usage.
    """
    id: Optional[str] = Field(None, description="Unique identifier for the usage record (e.g., DB primary key).")
    
    # User and Provider Context
    user_id: str = Field(..., description="The ID of the user who initiated the API call.")
    provider: str = Field(..., description="The service provider (e.g., 'OPENAI', 'ANTHROPIC', 'GEMINI').")
    model_name: str = Field(..., description="The specific model used (e.g., 'gpt-4o', 'claude-3-sonnet', 'gemini-2.5-flash').")
    
    # Usage Metrics
    input_tokens: int = Field(..., description="The number of prompt/input tokens consumed.")
    output_tokens: int = Field(..., description="The number of generated/output tokens consumed.")
    cost_usd: float = Field(..., description="Estimated cost of the call in USD.")
    
    # Optional metadata
    context_id: Optional[str] = Field(None, description="Optional ID of the context where the call originated (e.g., a specific chat session or document).")
    
    # Time Tracking
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the API call.")

    class Config:
        """Pydantic configuration for the model."""
        json_schema_extra = {
            "example": {
                "user_id": "user-abc123xyz",
                "provider": "OPENAI",
                "model_name": "gpt-4o",
                "input_tokens": 500,
                "output_tokens": 250,
                "cost_usd": 0.00375,
                "timestamp": "2024-05-15T10:00:00Z"
            }
        }

# ----------------------------------------------------------------------
# 2. AI Prompt Template Model
# ----------------------------------------------------------------------

class AIPromptTemplate(BaseModel):
    """
    Model for defining and storing reusable, parameterized prompt templates.
    """
    id: Optional[str] = Field(None, description="Unique identifier for the prompt template.")
    
    # Template Identification
    name: str = Field(..., description="A short, descriptive name for the template (e.g., 'Summarize Meeting Notes').")
    key: str = Field(..., description="A unique, URL-safe key for accessing the template (e.g., 'summarize_notes').")
    description: str = Field(..., description="A detailed explanation of the template's purpose and usage.")
    
    # Content Fields (designed to handle placeholders like {document_text})
    system_prompt: str = Field(..., description="The instructions for the AI model (the system role).")
    user_prompt_template: str = Field(..., description="The user-facing template with placeholders for dynamic content.")
    
    # Metadata and Control
    is_active: bool = Field(True, description="Whether the template is currently active and available for use.")
    required_parameters: List[str] = Field(default_factory=list, description="List of required placeholder names (e.g., ['document_text', 'tone']).")
    
    class Config:
        """Pydantic configuration for the model."""
        json_schema_extra = {
            "example": {
                "name": "Analyze Technical Report",
                "key": "analyze_report",
                "description": "Analyzes a technical report and extracts key findings, risks, and next steps.",
                "system_prompt": "You are an expert project manager. Your task is to analyze a technical document and extract structured data.",
                "user_prompt_template": "Analyze the following report in a {tone} tone, focusing on technical feasibility:\n\n---\n{report_text}\n---",
                "required_parameters": ["report_text", "tone"]
            }
        }

# ----------------------------------------------------------------------
# Example of a structured output schema that could be used by a template
# ----------------------------------------------------------------------

class SummaryOutput(BaseModel):
    """Example schema for a structured output generation."""
    title: str = Field(description="The generated title for the summary.")
    key_findings: List[str] = Field(description="A bulleted list of the most critical findings.")
    action_items: List[str] = Field(description="A list of required next steps or actions.")