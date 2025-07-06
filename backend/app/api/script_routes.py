"""
API routes for script generation
"""

import time
from fastapi import APIRouter, HTTPException, status, Request

from app.models.schemas import (
    ScenarioRequest, ScriptResponse, ErrorResponse, 
    ScriptValidationRequest, ScriptValidationResponse
)
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

@router.post("/validate", response_model=ScriptValidationResponse, tags=["Script Validation"])
async def validate_script(request: Request, validation_request: ScriptValidationRequest):
    """
    Validate a K6 script for quality and production readiness
    
    Args:
        validation_request: ScriptValidationRequest containing the script to validate
        
    Returns:
        ScriptValidationResponse with quality assessment and suggestions
    """
    try:
        script = validation_request.script
        
        logger.info("Validating K6 script for quality assessment")
        
        # Get AI service and validate script
        ai_service = get_ai_service()
        validation_report = await ai_service.validate_and_improve_script(script)
        
        logger.info(f"Script validation completed: {validation_report['quality_rating']}")
        
        return ScriptValidationResponse(**validation_report)
        
    except AIServiceError as e:
        logger.error(f"AI service error during validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during script validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during script validation"
        )


@router.post("/generate-enhanced", response_model=ScriptResponse, tags=["Enhanced Script Generation"])
async def generate_enhanced_script(request: Request, scenario: ScenarioRequest):
    """
    Generate a production-ready K6 script with enhanced validation and quality assurance
    
    Args:
        scenario: ScenarioRequest containing the scenario description
        
    Returns:
        ScriptResponse containing the generated k6 script with quality report
    """
    try:
        logger.info("Generating enhanced K6 script with quality validation")
        
        # Generate script using the internal function
        script_response = await _generate_script_internal(scenario.scenario_description)
        
        # Validate the generated script quality
        ai_service = get_ai_service()
        validation_report = await ai_service.validate_and_improve_script(script_response.script)
        
        # Add quality information to response
        script_response.metadata = {
            "quality_score": validation_report["quality_score"],
            "quality_rating": validation_report["quality_rating"],
            "production_ready": validation_report["overall_assessment"]["production_ready"],
            "validation_warnings": validation_report.get("warnings", []),
            "recommendations": validation_report.get("recommendations", [])
        }
        
        logger.info(f"Enhanced script generated with quality: {validation_report['quality_rating']}")
        
        return script_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during enhanced script generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during enhanced script generation"
        )
