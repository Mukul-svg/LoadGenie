import json
import logging
import os
from typing import Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import warnings
from dotenv import load_dotenv

# Suppress Pydantic warning from google-genai library
warnings.filterwarnings("ignore", message=".*<built-in function any> is not a Python type.*", category=UserWarning)

from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class AIService:
    def __init__(self, max_retries: int = 3, timeout: int = 60):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash"
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.max_retries = max_retries
        self.timeout = timeout
    
    def _generate_sync(self, description: str) -> Dict[str, str]:
        """Synchronous generation method to be called in thread executor"""
        retry_count = 0
        last_exception = None
        
        while retry_count < self.max_retries:
            try:
                logger.info(f"Generation attempt {retry_count + 1}/{self.max_retries}")
                
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=description),
                        ],
                    ),
                ]
                
                generate_content_config = types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json",
                    response_schema=genai.types.Schema(
                        type=genai.types.Type.OBJECT,
                        required=["k6_script"],
                        properties={
                            "k6_script": genai.types.Schema(
                                type=genai.types.Type.STRING,
                            ),
                        },
                    ),
                    system_instruction=[
                        types.Part.from_text(
                            text="""You are a performance engineer expert. Write a k6 JavaScript script that performs the scenario given by user. 
                            REQUIREMENTS:
                            - Return only valid, executable k6 JavaScript code
                            - Include proper imports (http, sleep, check, etc.)
                            - Set appropriate virtual users and duration based on the scenario
                            - Add response validation with checks when appropriate
                            - Use realistic think time with sleep()
                            - Follow k6 best practices for load testing
                            - Make the script production-ready with proper error handling
                            - Return the response in JSON format with the key "k6_script"
                            """
                        ),
                    ],
                )

                # Collect the full response with timeout
                full_response = ""
                start_time = time.time()
                
                for chunk in self.client.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=generate_content_config,
                ):
                    if time.time() - start_time > self.timeout:
                        raise AIServiceError(f"Generation timeout after {self.timeout} seconds")
                        
                    if chunk.text:
                        full_response += chunk.text
                
                # Parse the JSON response
                if not full_response.strip():
                    raise AIServiceError("Empty response from AI service")
                    
                try:
                    result = json.loads(full_response)
                    
                    # Additional validation
                    if not result.get("k6_script"):
                        raise AIServiceError("Generated script is empty or missing")
                    
                    # Basic validation of k6 script content
                    script = result["k6_script"]
                    required_patterns = ["export default function", "http"]
                    missing_patterns = [p for p in required_patterns if p not in script]
                    
                    if missing_patterns:
                        logger.warning(f"Generated script missing patterns: {missing_patterns}")
                        # Don't fail, but log the warning
                    
                    logger.info("✅ Successfully generated and validated k6 script")
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI response as JSON: {e}")
                    logger.error(f"Raw response: {full_response[:500]}...")
                    raise AIServiceError(f"Invalid JSON response from AI service: {e}")
                    
            except Exception as e:
                last_exception = e
                retry_count += 1
                
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Generation failed (attempt {retry_count}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All generation attempts failed: {e}")
        
        # If we get here, all retries failed
        if isinstance(last_exception, AIServiceError):
            raise last_exception
        raise AIServiceError(f"Failed to generate content after {self.max_retries} attempts: {str(last_exception)}")
    
    async def generate_k6_script(self, description: str) -> Dict[str, str]:
        """
        Generate a k6 script based on the scenario description
        
        Args:
            description: The scenario description for load testing
            
        Returns:
            Dict containing the generated k6 script
            
        Raises:
            AIServiceError: If generation fails
        """
        if not description or not description.strip():
            raise AIServiceError("Description cannot be empty")
            
        if len(description.strip()) < 10:
            raise AIServiceError("Description too short, please provide more details")
            
        logger.info(f"Generating k6 script for description: {description[:100]}...")
        start_time = time.time()
        
        try:
            # Run the synchronous generation in a thread executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._generate_sync, 
                description
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Script generation completed in {generation_time:.2f} seconds")
            
            return result
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_k6_script: {e}")
            raise AIServiceError(f"Unexpected error: {str(e)}")

# Global AI service instance - will be initialized when imported
ai_service = None

def get_ai_service() -> AIService:
    """Get or create the AI service instance"""
    global ai_service
    if ai_service is None:
        ai_service = AIService()
    return ai_service

# For backward compatibility
ai_service = get_ai_service()