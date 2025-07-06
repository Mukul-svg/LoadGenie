"""
API routes for script generation
"""

import time
from fastapi import APIRouter, HTTPException, status, Request

from app.models.schemas import ScenarioRequest, ScriptResponse, ErrorResponse
from app.services.ai_service import get_ai_service, AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

async def _generate_script_internal(scenario_description: str) -> ScriptResponse:
    """
    Internal function to generate k6 script
    
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
        ai_service = get_ai_service()
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

@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script(request: Request) -> ScriptResponse:
    """
    Generate a k6 load testing script based on scenario description
    
    This endpoint handles both JSON and form data automatically for backward compatibility.
    
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

@router.post("/generate-script-form", response_model=ScriptResponse)
async def generate_script_form(request: Request) -> ScriptResponse:
    """
    Generate a k6 load testing script based on scenario description (Form data)
    
    Args:
        scenario_description: The scenario description from form data
        
    Returns:
        ScriptResponse containing the generated k6 script
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        form_data = await request.form()
        scenario_description = form_data.get("scenario_description")
        
        if not scenario_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scenario_description is required"
            )
        
        return await _generate_script_internal(scenario_description)
    except Exception as e:
        logger.error(f"Error processing form request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing request: {str(e)}"
        )

@router.post("/api/generate-script", response_model=ScriptResponse)
async def generate_script_unified(request: Request) -> ScriptResponse:
    """
    Unified endpoint that can handle both JSON and form data
    
    This endpoint automatically detects the content type and processes accordingly:
    - application/json: Expects {"scenario_description": "..."}
    - multipart/form-data: Expects scenario_description field
    - application/x-www-form-urlencoded: Expects scenario_description field
    """
    return await generate_script(request)
