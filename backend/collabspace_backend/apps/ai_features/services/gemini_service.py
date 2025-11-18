import logging
import json
from typing import List, Dict, Any, Optional

# Gemini SDK Imports
from google import genai
from google.genai import types
from google.genai.errors import APIError, ResourceExhausted, DeadlineExceeded
from pydantic import BaseModel, Field

# CollabSpace Placeholder Imports (Assumed to exist)
from .base_ai_service import BaseAIService, User, settings 

logger = logging.getLogger(__name__)

# --- Gemini Model & Pricing Configuration ---
# Using Gemini 2.5 Flash for chat/completion
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_INPUT_PRICE_PER_M_TOKENS = 0.15 
GEMINI_OUTPUT_PRICE_PER_M_TOKENS = 1.25 

# Using gemini-embedding-001 for embeddings
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_PRICE_PER_M_TOKENS = 0.15 

# --- Pydantic Schema Example ---
class SubTask(BaseModel):
    title: str = Field(description="A concise title for the subtask.")
    description: str = Field(description="A detailed description of the subtask.")
    estimated_hours: int = Field(description="An estimated effort in hours (integer) for the subtask.")


class GeminiService(BaseAIService):
    """
    AI service provider using the Google Gemini API. 
    Handles text generation, chat, structured JSON, embeddings, and basic content moderation.
    """
    
    def __init__(self):
        super().__init__()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL 
        self.embedding_model = EMBEDDING_MODEL
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculates the estimated cost based on token usage for a given model."""
        
        if model == self.embedding_model:
            cost = (input_tokens / 1_000_000) * EMBEDDING_PRICE_PER_M_TOKENS
            return cost
        elif model == self.model or model == GEMINI_MODEL:
            input_cost = (input_tokens / 1_000_000) * GEMINI_INPUT_PRICE_PER_M_TOKENS
            output_cost = (output_tokens / 1_000_000) * GEMINI_OUTPUT_PRICE_PER_M_TOKENS
            return input_cost + output_cost
        else:
            return 0.0

    def count_tokens(self, contents: List[types.Part], model: Optional[str] = None) -> int:
        """Count tokens in a list of contents using the API."""
        model_name = model or self.model
        try:
            # Ensure contents is wrapped as a list of Content objects if necessary
            contents_list = contents if isinstance(contents[0], types.Content) else [types.Content(parts=contents)]
            
            response = self.client.models.count_tokens(
                model=model_name,
                contents=contents_list
            )
            return response.total_tokens
        except APIError as e:
            logger.error(f"Error counting tokens for {model_name}: {e}")
            return 0

    def _generate_content_with_retry(
        self,
        contents: List[types.Content],
        user: User,
        config: Optional[types.GenerateContentConfig] = None,
        model: Optional[str] = None
    ) -> types.GenerateContentResponse:
        """Core logic for calling the Gemini API with retry, rate limit, and usage tracking."""
        
        final_model = model or self.model
            
        for attempt in range(1, self.max_retries + 1):
            
            if not self.handle_rate_limit(user):
                 # Wait briefly if internal limit hit, then check again on the next attempt
                 if attempt < self.max_retries:
                     # This logic assumes self.handle_error manages the sleep, but 
                     # we'll raise immediately here if we can't proceed.
                     raise ResourceExhausted("Internal Rate Limit exceeded.")

            try:
                # 1. API Call
                response = self.client.models.generate_content(
                    model=final_model,
                    contents=contents,
                    config=config,
                )
                
                # 2. Safety Check / Empty Response
                if not response.candidates or not response.text:
                    if response.candidates and response.candidates[0].finish_reason.name == "SAFETY":
                        raise APIError("Response blocked due to safety settings.")
                    raise APIError("Empty response text received or no candidates generated.")

                # 3. Usage Tracking (Happens only on successful attempt)
                usage_metadata = response.usage_metadata
                input_tokens = usage_metadata.prompt_token_count
                output_tokens = usage_metadata.candidates_token_count
                cost = self._calculate_cost(input_tokens, output_tokens, final_model)
                self.track_usage(user, input_tokens, output_tokens, cost, final_model)
                
                return response
                
            except (ResourceExhausted, DeadlineExceeded, APIError, Exception) as e:
                # 4. Error Handling & Retry
                if self.handle_error(e, attempt):
                    continue
                else:
                    raise
        
        # If max retries are exceeded
        raise APIError("Gemini API call failed after max retries.")

    ## -------------------- Public Methods --------------------

    def generate_completion(
        self, 
        prompt: str, 
        user: User, 
        max_output_tokens: Optional[int] = None, 
        temperature: float = 0.7
    ) -> str:
        """Generate text completion from a single prompt."""
        
        contents = [types.Content(role="user", parts=[types.Part.from_text(prompt)])]
        config = types.GenerateContentConfig(temperature=temperature, max_output_tokens=max_output_tokens)
        
        try:
            response = self._generate_content_with_retry(contents, user, config)
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate completion: {e}")
            return f"AI Service Error: Could not generate completion. Details: {e}"

    def generate_chat_completion(self, messages: List[Dict[str, str]], user: User, **kwargs) -> str:
        """Generate chat completion from a list of messages."""
        
        gemini_contents = []
        for message in messages:
            role = "model" if message["role"] == "assistant" else "user"
            gemini_contents.append(
                types.Content(role=role, parts=[types.Part.from_text(message["content"])])
            )
        
        config = types.GenerateContentConfig(
            temperature=kwargs.get('temperature', 0.7),
            max_output_tokens=kwargs.get('max_output_tokens', 2048)
        )
        
        try:
            response = self._generate_content_with_retry(gemini_contents, user, config)
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {e}")
            return f"AI Service Error: Could not generate chat response. Details: {e}"
            
    def generate_structured_json(
        self, 
        prompt: str, 
        user: User, 
        schema: BaseModel,
        max_output_tokens: Optional[int] = 2048,
        temperature: float = 0.0,
    ) -> Any:
        """Generate a response that strictly adheres to a Pydantic schema."""
        contents = [types.Content(role="user", parts=[types.Part.from_text(prompt)])]
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_schema=schema,
        )

        try:
            response = self._generate_content_with_retry(contents, user, config)
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Failed to generate structured JSON: {e}")
            return []
            
    def generate_embedding(self, text: str, user: User) -> List[float]:
        """Generate text embedding for search using gemini-embedding-001."""
        if not self.handle_rate_limit(user):
            raise ResourceExhausted("Internal Rate Limit exceeded.")

        try:
            result = self.client.models.embed_content(
                model=self.embedding_model,
                content=text,
            )
            
            # Manually track usage since embed_content doesn't return usage_metadata
            input_tokens = self.count_tokens([types.Part.from_text(text)], model=self.embedding_model)
            cost = self._calculate_cost(input_tokens, 0, self.embedding_model)
            self.track_usage(user, input_tokens, 0, cost, self.embedding_model)
            
            return result.embedding.values
            
        except Exception as e:
            self.handle_error(e, 1)
            raise

    def moderate_content(self, text: str, user: User) -> bool:
        """
        Check content for policy violations using the Gemini API's built-in safety filters 
        and an explicit model prompt check. Returns True if content is safe.
        """
        
        prompt = f"""
        Analyze the following text for severe policy violations (hate speech, self-harm, sexual, harassment, dangerous content).
        If the content is safe and does not violate policies, output 'SAFE'. If it is unsafe, output 'UNSAFE' and the reason.
        
        TEXT: "{text}"
        """
        
        try:
            contents = [types.Content(role="user", parts=[types.Part.from_text(prompt)])]
            config = types.GenerateContentConfig(temperature=0.0, max_output_tokens=50)

            response = self._generate_content_with_retry(contents, user, config)
            
            result_text = response.text.strip().upper()
            
            # 1. Check for the model's explicit 'UNSAFE' determination
            is_safe = "UNSAFE" not in result_text
            
            # 2. Check the native safety ratings for definitive blocks
            safety_blocked = False
            if response.candidates and response.candidates[0].safety_ratings:
                for rating in response.candidates[0].safety_ratings:
                    # BLOCK_MEDIUM_AND_ABOVE is the default threshold
                    if rating.probability.name in ["MEDIUM", "HIGH"]:
                        safety_blocked = True
                        break

            return is_safe and (not safety_blocked)

        except Exception as e:
            # If the check fails (e.g., API error), log and default to blocking the content
            self.handle_error(e, 1)
            return False