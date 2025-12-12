from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model

from .gemini_service import GeminiService 
from .base_ai_service import BaseAIService

User = get_user_model()


class CodeAIService(BaseAIService):
    """Service for AI-powered code analysis, generation, and review."""
    
    FEATURE_TYPE = 'code_ai'
    
    def __init__(self, provider: str = 'gemini'):
        super().__init__()
        self.ai = GeminiService() if provider == 'gemini' else self._get_openai_service()
    
    def _get_openai_service(self):
        """Placeholder for OpenAI service integration."""
        from .openai_service import OpenAIService
        return OpenAIService()

    def review_code(self, user: User, workspace, code: str, language: str, **kwargs) -> Dict[str, str]:
        """Review code and suggest improvements (security, style, performance)."""
        prompt = f"""
Perform a professional code review for the following {language} code snippet. 
Focus on security vulnerabilities, best practices, and performance issues. 
Provide a list of suggested changes with brief explanations.

CODE:

{code}
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )
        return {'review': response.get('text', 'Failed to review code.')}
        
    def generate_code(self, user: User, workspace, description: str, language: str, **kwargs) -> Dict[str, str]:
        """Generate code from description."""
        prompt = f"""
Generate a complete, production-ready code snippet in {language} that fulfills the following requirement:

REQUIREMENT: {description}

Return only the code block, starting and ending with the correct markdown fence for {language}.
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8048,
            use_pro=False
        )
        return {'code': response.get('text', 'Failed to generate code.')}
        
    def explain_code(self, user: User, workspace, code: str, language: str, **kwargs) -> Dict[str, str]:
        """Explain what code does, step-by-step."""
        prompt = f"""
Explain the purpose and function of the following {language} code in clear, simple terms. 
Break down the explanation into easy-to-understand steps.

CODE:

{code}
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )
        return {'explanation': response.get('text', 'Failed to explain code.')}
        
    def debug_code(self, user: User, workspace, code: str, error_message: str, **kwargs) -> Dict[str, str]:
        """Help debug code by suggesting fixes for a given error."""
        prompt = f"""
Analyze the following code and error message. Identify the root cause of the error and provide a corrected version of the code snippet.

CODE:

{code}

ERROR:

{error_message}

First, state the fix. Second, provide the full corrected code snippet in a markdown code block.
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8024,
            use_pro=False
        )
        return {'debug_solution': response.get('text', 'Failed to debug code.')}
        
    def generate_tests(self, user: User, workspace, code: str, language: str, **kwargs) -> Dict[str, str]:
        """Generate unit tests for the given code."""
        prompt = f"""
Generate comprehensive unit tests for the provided {language} code. Use the standard testing framework for this language (e.g., pytest, JUnit, Go testing). 
Include tests for happy paths, edge cases, and error handling.

Return only the test code in a markdown code block.

CODE:

{code}
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8500,
            use_pro=False
        )
        return {'tests': response.get('text', 'Failed to generate tests.')}
    
    def refactor_code(self, user: User, workspace, code: str, language: str, refactor_goal: str = "improve readability", **kwargs) -> Dict[str, str]:
        """Refactor code based on specified goal."""
        prompt = f"""
Refactor the following {language} code to {refactor_goal}.
Maintain the same functionality but improve the code structure.

CODE:

{code}

Provide the refactored code with a brief explanation of changes made.
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=False
        )
        return {'refactored_code': response.get('text', 'Failed to refactor code.')}
    
    def convert_code(self, user: User, workspace, code: str, from_language: str, to_language: str, **kwargs) -> Dict[str, str]:
        """Convert code from one programming language to another."""
        prompt = f"""
Convert the following {from_language} code to {to_language}.
Maintain the same logic and functionality.

{from_language.upper()} CODE:

{code}

Provide only the converted {to_language} code in a markdown code block.
"""
        response = self.ai.generate_completion(
            user=user,
            workspace=workspace,
            prompt=prompt,
            feature_type=self.FEATURE_TYPE,
            max_tokens=8000,
            use_pro=True  # Use Pro for better language understanding
        )
        return {'converted_code': response.get('text', 'Failed to convert code.')}