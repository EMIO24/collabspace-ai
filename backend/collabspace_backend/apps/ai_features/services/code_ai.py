from typing import List, Dict, Any, Optional

# CollabSpace Placeholder Imports
from .base_ai_service import User 
from .gemini_service import GeminiService 

class CodeAIService:
    def __init__(self, provider: str = 'gemini', user: Optional[User] = None):
        self.user = user or User(id=999, email="default_ai_user@collabspace.com")
        self.ai = GeminiService() if provider == 'gemini' else self._get_openai_service()
    
    def _get_openai_service(self):
        from .openai_service import OpenAIService
        return OpenAIService()

    def review_code(self, code: str, language: str) -> str:
        """Review code and suggest improvements (security, style, performance)."""
        prompt = f"""
        Perform a professional code review for the following {language} code snippet. 
        Focus on security vulnerabilities, best practices, and performance issues. 
        Provide a list of suggested changes with brief explanations.
        
        CODE:\n\n{code}
        """
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=1500, temperature=0.2)
        
    def generate_code(self, description: str, language: str) -> str:
        """Generate code from description."""
        prompt = f"""
        Generate a complete, production-ready code snippet in {language} that fulfills the following requirement:
        
        REQUIREMENT: {description}
        
        Return only the code block, starting and ending with the correct markdown fence for {language}.
        """
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=2048, temperature=0.5)
        
    def explain_code(self, code: str, language: str) -> str:
        """Explain what code does, step-by-step."""
        prompt = f"""
        Explain the purpose and function of the following {language} code in clear, simple terms. 
        Break down the explanation into easy-to-understand steps.
        
        CODE:\n\n{code}
        """
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=800, temperature=0.1)
        
    def debug_code(self, code: str, error_message: str) -> str:
        """Help debug code by suggesting fixes for a given error."""
        prompt = f"""
        Analyze the following code and error message. Identify the root cause of the error and provide a corrected version of the code snippet.
        
        LANGUAGE: Determined from context.
        CODE:\n\n{code}
        ERROR:\n\n{error_message}
        
        First, state the fix. Second, provide the full corrected code snippet in a markdown code block.
        """
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=1024, temperature=0.1)
        
    def generate_tests(self, code: str, language: str) -> str:
        """Generate unit tests for the given code."""
        prompt = f"""
        Generate comprehensive unit tests for the provided {language} code. Use the standard testing framework for this language (e.g., pytest, JUnit, Go testing). 
        Include tests for happy paths, edge cases, and error handling.
        
        Return only the test code in a markdown code block.
        CODE:\n\n{code}
        """
        return self.ai.generate_completion(prompt, user=self.user, max_output_tokens=1500, temperature=0.5)