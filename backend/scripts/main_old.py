import logging
from fastapi import FastAPI, HTTPException, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Union, Optional
import time
import json

from ai_service import ai_service, AIServiceError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LoadGenie API",
    description="AI-powered k6 load testing script generator",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScenarioRequest(BaseModel):
    scenario_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of the load testing scenario"
    )

class ScriptResponse(BaseModel):
    script: str = Field(..., description="Generated k6 JavaScript script")
    generated_at: str = Field(..., description="Timestamp when script was generated")
    scenario_description: str = Field(..., description="Original scenario description")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: str = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")

@app.exception_handler(AIServiceError)
async def ai_service_exception_handler(request, exc: AIServiceError):
    """Handle AI service specific errors"""
    logger.error(f"AI Service Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error="AI service error",
            detail=str(exc),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        ).dict()
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc: ValueError):
    """Handle validation errors"""
    logger.error(f"Validation Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="Validation error",
            detail=str(exc),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        ).dict()
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

@app.post("/generate-script", response_model=ScriptResponse)
async def generate_script(request: Request) -> ScriptResponse:
    """
    Generate a k6 load testing script based on scenario description
    
    This endpoint now handles both JSON and form data automatically for backward compatibility.
    
    Returns:
        ScriptResponse containing the generated k6 script
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            # Handle JSON payload
            body = await request.json()
            scenario_description = body.get("scenario_description")
        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            # Handle form data
            form_data = await request.form()
            scenario_description = form_data.get("scenario_description")
        else:
            # Try to parse as JSON first, then form data
            try:
                body = await request.json()
                scenario_description = body.get("scenario_description")
            except:
                form_data = await request.form()
                scenario_description = form_data.get("scenario_description")
        
        if not scenario_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scenario_description is required"
            )
            
        # Validate description length
        if len(scenario_description.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario description must be at least 10 characters long"
            )
        
        return await _generate_script_internal(scenario_description)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/generate-script-form", response_model=ScriptResponse)
async def generate_script_form(scenario_description: str = Form(...)) -> ScriptResponse:
    """
    Generate a k6 load testing script based on scenario description (Form data)
    
    Args:
        scenario_description: The scenario description from form data
        
    Returns:
        ScriptResponse containing the generated k6 script
        
    Raises:
        HTTPException: If generation fails
    """
    return await _generate_script_internal(scenario_description)

@app.post("/api/generate-script", response_model=ScriptResponse)
async def generate_script_unified(request: Request) -> ScriptResponse:
    """
    Unified endpoint that can handle both JSON and form data
    
    This endpoint automatically detects the content type and processes accordingly:
    - application/json: Expects {"scenario_description": "..."}
    - multipart/form-data: Expects scenario_description field
    - application/x-www-form-urlencoded: Expects scenario_description field
    """
    try:
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            # Handle JSON payload
            body = await request.json()
            scenario_description = body.get("scenario_description")
        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            # Handle form data
            form_data = await request.form()
            scenario_description = form_data.get("scenario_description")
        else:
            # Try to parse as JSON first, then form data
            try:
                body = await request.json()
                scenario_description = body.get("scenario_description")
            except:
                form_data = await request.form()
                scenario_description = form_data.get("scenario_description")
        
        if not scenario_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scenario_description is required"
            )
            
        # Validate description length
        if len(scenario_description.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scenario description must be at least 10 characters long"
            )
        
        return await _generate_script_internal(scenario_description)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing request: {str(e)}"
        )

async def _generate_script_internal(scenario_description: str) -> ScriptResponse:
    """
    Generate a k6 load testing script based on scenario description
    
    Args:
        scenario_description: The scenario description string
        
    Returns:
        ScriptResponse containing the generated k6 script
        
    Raises:
        HTTPException: If generation fails
    """
    start_time = time.time()
    logger.info(f"Received script generation request: {scenario_description[:100]}...")
    
    try:
        # Validate input
        description = scenario_description.strip()
        if not description:
            raise ValueError("Scenario description cannot be empty")
        
        # Generate script using AI service
        result = await ai_service.generate_k6_script(description)
        
        # Validate AI response
        if not isinstance(result, dict) or 'k6_script' not in result:
            logger.error(f"Invalid AI response format: {result}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response format from AI service"
            )
        
        k6_script = result['k6_script']
        if not k6_script or not k6_script.strip():
            logger.error("Generated k6 script is empty")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generated script is empty"
            )
        
        # Log success
        generation_time = time.time() - start_time
        logger.info(f"Successfully generated script in {generation_time:.2f} seconds")
        
        # Return response
        response = ScriptResponse(
            script=k6_script,
            generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            scenario_description=description
        )
        
        return response
        
    except AIServiceError as e:
        # Let the exception handler deal with this
        raise e
    except ValueError as e:
        # Let the exception handler deal with this
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in generate_script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the script"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
