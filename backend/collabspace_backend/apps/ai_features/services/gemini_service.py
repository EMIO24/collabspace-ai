import json
from typing import List, Dict, Any, Optional, Union
from google import genai
from google.genai.errors import ResourceExhaustedError, APIError
from google.genai import types
# Assume BaseAIService, settings, logger are accessible/imported as above

# Rename the file from openai_service.py to gemini_service.py
class GeminiService(BaseAIService):
    """Concrete service for interacting with the Google Gemini API."""
    
    def __init__(self):
        super().__init__()
        # Initialize client using API key from settings
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
        self.embedding_model = settings.GEMINI_EMBEDDING_MODEL

    def count_tokens(self, parts: List[Any], model: str = settings.GEMINI_MODEL) -> int:
        """Count tokens in text or messages using the Gemini API."""
        try:
            # The SDK handles counting for different types (text, parts, messages)
            response = self.client.models.count_tokens(model=model, contents=parts)
            return response.total_tokens
        except APIError as e:
            logger.error(f"Gemini token counting failed: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error during token counting: {e}")
            return 0

    def _call_api_with_retry(self, api_call: callable, contents: List[Any], user_id: str, model: str, **kwargs) -> Optional[Any]:
        """Generic method to handle API calls with retry logic and rate limit check."""
        
        if not self.handle_rate_limit(user_id):
            logger.warning(f"User {user_id} hit application-level rate limit.")
            return None # Return None to trigger fallback
        
        for attempt in range(self.max_retries):
            try:
                # 1. API Call
                response = api_call(model=model, contents=contents, **kwargs)
                return response
            except Exception as e: # Catch all exceptions including APIError, ResourceExhaustedError
                if attempt < self.max_retries - 1 and self.handle_error(e, attempt):
                    continue
                else:
                    logger.error(f"Gemini API call failed after {attempt+1} attempts.")
                    return None
        return None
    
    def _process_completion_response(self, response: Optional[Any], user_id: str, model: str, contents: List[Any]) -> Dict[str, Any]:
        """Processes and tracks usage for a successful or failed completion response."""
        if not response:
            return {"success": False, "content": self.FALLBACK_RESPONSE}
        
        try:
            # Extract content
            content = response.text
            
            # Extract token usage (Gemini includes prompt and completion tokens)
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            
            # Track usage
            self.track_usage(
                user_id=user_id, 
                model=model, 
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Check for safety blocks or failure reason
            if not content and response.prompt_feedback.block_reason:
                 logger.warning(f"Request blocked: {response.prompt_feedback.block_reason.name}")
                 return {"success": False, "content": "The request was blocked due to safety settings or policy violation."}
            
            return {"success": True, "content": content, "usage": usage_metadata}
            
        except (AttributeError, IndexError, TypeError) as e:
            logger.error(f"Failed to parse Gemini response structure: {e}")
            return {"success": False, "content": self.FALLBACK_RESPONSE}
            
    def generate_completion(self, prompt: str, user_id: str = "system", temperature: float = 0.7, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate text completion using the generate_content endpoint."""
        
        # Structure the prompt as contents for the API
        contents = [types.Content(parts=[types.Part.from_text(prompt)])]
        
        # Configure generation parameters
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        api_call = lambda **args: self.client.models.generate_content(**args)
        
        response = self._call_api_with_retry(
            api_call=api_call,
            contents=contents,
            user_id=user_id,
            model=self.model,
            config=config
        )
        
        return self._process_completion_response(response, user_id, self.model, contents)

    def generate_chat_completion(self, messages: List[Dict[str, str]], user_id: str = "system", **kwargs) -> Dict[str, Any]:
        """Generate chat completion. Gemini handles conversation history via the `chats` service, 
        but we simulate a single turn using generate_content for simplicity and consistency."""
        
        # Convert dictionary list to Content objects
        contents = [
            types.Content(
                role=msg['role'].replace('user', 'user').replace('assistant', 'model'), # Map roles
                parts=[types.Part.from_text(msg['content'])]
            )
            for msg in messages
        ]

        config = types.GenerateContentConfig(
            temperature=kwargs.get('temperature', 0.7),
            max_output_tokens=kwargs.get('max_tokens')
        )

        api_call = lambda **args: self.client.models.generate_content(**args)
        
        response = self._call_api_with_retry(
            api_call=api_call,
            contents=contents,
            user_id=user_id,
            model=self.model,
            config=config
        )
        
        return self._process_completion_response(response, user_id, self.model, contents)

    def generate_structured_completion(self, prompt: str, json_schema: Dict[str, Any], user_id: str = "system", **kwargs) -> Dict[str, Any]:
        """Generates a completion constrained to a JSON schema."""
        
        contents = [types.Content(parts=[types.Part.from_text(prompt)])]
        
        # Convert JSON schema dictionary to a Schema object
        schema = types.Schema.from_dict(json_schema)
        
        config = types.GenerateContentConfig(
            temperature=kwargs.get('temperature', 0.1),
            response_mime_type="application/json",
            response_schema=schema
        )
        
        api_call = lambda **args: self.client.models.generate_content(**args)
        
        response = self._call_api_with_retry(
            api_call=api_call,
            contents=contents,
            user_id=user_id,
            model=self.model,
            config=config
        )
        
        processed_response = self._process_completion_response(response, user_id, self.model, contents)
        
        if processed_response["success"]:
            try:
                # Attempt to parse the content to ensure it's valid JSON
                json_data = json.loads(processed_response["content"])
                processed_response["content"] = json_data
            except json.JSONDecodeError as e:
                logger.error(f"Structured response was not valid JSON: {e}")
                processed_response["success"] = False
                processed_response["content"] = self.FALLBACK_RESPONSE
        
        return processed_response


    def generate_embedding(self, text: Union[str, List[str]], user_id: str = "system") -> Dict[str, Any]:
        """Generate text embedding for search."""
        texts = [text] if isinstance(text, str) else text
        
        # Calculate token count manually for tracking (or rely on API call if using a different method)
        input_tokens = sum(self.count_tokens([t], model=self.embedding_model) for t in texts)
        
        api_call = lambda **args: self.client.models.embed_content(**args)
        
        # The official embed_content does not take a user_id, so we pass it only for rate limit check
        response = self._call_api_with_retry(
            api_call=api_call,
            contents=texts, # texts is the input for embed_content
            user_id=user_id,
            model=self.embedding_model,
        )
        
        if not response:
            return {"success": False, "embedding": []}

        # Track usage
        self.track_usage(
            user_id=user_id,
            model=self.embedding_model,
            input_tokens=input_tokens,
            output_tokens=0
        )
        
        try:
            # Embedding response structure: response.embedding or response.embeddings
            embeddings = [d.values for d in response.embeddings] if hasattr(response, 'embeddings') else [response.embedding.values]
            return {"success": True, "embedding": embeddings}
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to parse embedding response: {e}")
            return {"success": False, "embedding": []}

    # Note: Gemini/Google AI generally relies on integrated safety features rather than a separate 'moderation' API call.
    # The safety settings are applied automatically during content generation/chat.
    # The 'moderate_content' function is therefore omitted or simplified, as it's handled implicitly.