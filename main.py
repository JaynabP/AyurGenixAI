from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
from dotenv import load_dotenv

from simple_rag_processor import AyurvedicRAGProcessor
from enhanced_prescription import (
    EnhancedPrescriptionGenerator,
    PatientInfo
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AyurGenixAI - Ayurvedic Prescription Generator",
    description="AI-powered Ayurvedic prescription generator using RAG model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for RAG processor and prescription generator
rag_processor = None
prescription_generator = None


class PatientRequest(BaseModel):
    """Patient information request model"""
    name: str = Field(..., description="Patient's name")
    age: int = Field(..., ge=1, le=120, description="Patient's age")
    gender: str = Field(..., description="Patient's gender")
    constitution_dosha: str = Field(
        ...,
        description="Patient's constitution dosha (Vata/Pitta/Kapha)"
    )
    symptoms: List[str] = Field(
        ...,
        description="List of symptoms"
    )
    doctor_diagnosis: str = Field(
        ...,
        description="Doctor's diagnosis"
    )


class PrescriptionResponse(BaseModel):
    """Prescription response model"""
    success: bool
    prescription: Optional[str] = None
    patient_info: Optional[dict] = None
    similar_cases_count: Optional[int] = None
    json_format: Optional[dict] = None
    error_message: Optional[str] = None


class MedicationResponse(BaseModel):
    """Medication and lifestyle response model"""
    success: bool
    patient_info: Optional[dict] = None
    ayurvedic_medicines: Optional[List[str]] = None
    lifestyle_recommendations: Optional[List[str]] = None
    similar_cases_count: Optional[int] = None
    error_message: Optional[str] = None


class DietResponse(BaseModel):
    """Diet recommendations response model"""
    success: bool
    patient_info: Optional[dict] = None
    diet_recommendations: Optional[dict] = None
    diet_chart: Optional[str] = None
    similar_cases_count: Optional[int] = None
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    rag_processor_status: str
    prescription_generator_status: str
    collection_stats: Optional[dict] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG processor and prescription generator on startup"""
    global rag_processor, prescription_generator
    
    try:
        logger.info("Initializing AyurGenixAI system...")
        
        # Get environment variables
        csv_path = os.getenv("CSV_PATH", "./AyurGenixAI_Dataset.csv")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY is required")
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found at: {csv_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Initialize RAG processor
        logger.info("Initializing RAG processor...")
        rag_processor = AyurvedicRAGProcessor(csv_path)
        
        # Initialize prescription generator
        logger.info("Initializing prescription generator...")
        prescription_generator = EnhancedPrescriptionGenerator(gemini_api_key)
        
        logger.info("AyurGenixAI system initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with welcome message"""
    return {
        "message": "Welcome to AyurGenixAI - Your Ayurvedic Health Companion",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_prescription": "/generate-prescription",
            "search_cases": "/search-cases"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check RAG processor status
        rag_status = (
            "healthy" if rag_processor is not None
            else "not_initialized"
        )
        
        # Check prescription generator status
        prescription_status = (
            "healthy" if prescription_generator is not None
            else "not_initialized"
        )
        
        # Get collection stats if available
        collection_stats = None
        if rag_processor:
            collection_stats = rag_processor.get_collection_stats()
        
        overall_status = (
            "healthy" if rag_status == "healthy" and
            prescription_status == "healthy" else "unhealthy"
        )
        
        return HealthResponse(
            status=overall_status,
            rag_processor_status=rag_status,
            prescription_generator_status=prescription_status,
            collection_stats=collection_stats
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            rag_processor_status="error",
            prescription_generator_status="error"
        )


@app.post("/generate-prescription", response_model=PrescriptionResponse)
async def generate_prescription(patient_request: PatientRequest):
    """
    Generate a comprehensive Ayurvedic prescription for a patient
    """
    try:
        if not rag_processor or not prescription_generator:
            raise HTTPException(
                status_code=500,
                detail="System not properly initialized"
            )
        
        # Convert request to PatientInfo
        patient_info = PatientInfo(
            name=patient_request.name,
            age=patient_request.age,
            gender=patient_request.gender,
            constitution_dosha=patient_request.constitution_dosha,
            symptoms=patient_request.symptoms,
            doctor_diagnosis=patient_request.doctor_diagnosis
        )
        
        # Search for similar cases using RAG
        logger.info(
            f"Searching for similar cases for patient: {patient_info.name}"
        )
        similar_cases = rag_processor.search_by_symptoms_and_dosha(
            symptoms=patient_info.symptoms,
            constitution_dosha=patient_info.constitution_dosha,
            diagnosis=patient_info.doctor_diagnosis,
            n_results=5
        )
        
        # Generate prescription using Gemini API
        logger.info("Generating prescription using Gemini API...")
        prescription_result = prescription_generator.generate_prescription(
            patient_info=patient_info,
            similar_cases=similar_cases,
            output_format="display"
        )
        
        return PrescriptionResponse(
            success=prescription_result["success"],
            prescription=prescription_result["display_format"],
            patient_info={
                "name": patient_info.name,
                "age": patient_info.age,
                "gender": patient_info.gender,
                "constitution_dosha": patient_info.constitution_dosha,
                "symptoms": patient_info.symptoms,
                "doctor_diagnosis": patient_info.doctor_diagnosis
            },
            similar_cases_count=prescription_result.get("similar_cases_count", 0),
            json_format=prescription_result.get("json_format", {})
        )
        
    except Exception as e:
        logger.error(f"Error generating prescription: {e}")
        return PrescriptionResponse(
            success=False,
            error_message=str(e)
        )


@app.post("/generate-medication", response_model=MedicationResponse)
async def generate_medication_and_lifestyle(patient_request: PatientRequest):
    """
    Generate Ayurvedic medications and lifestyle recommendations
    """
    try:
        if not rag_processor or not prescription_generator:
            raise HTTPException(
                status_code=500,
                detail="System not properly initialized"
            )
        
        # Convert request to PatientInfo
        patient_info = PatientInfo(
            name=patient_request.name,
            age=patient_request.age,
            gender=patient_request.gender,
            constitution_dosha=patient_request.constitution_dosha,
            symptoms=patient_request.symptoms,
            doctor_diagnosis=patient_request.doctor_diagnosis
        )
        
        # Search for similar cases
        logger.info(
            f"Searching for medication recommendations for: {patient_info.name}"
        )
        similar_cases = rag_processor.search_by_symptoms_and_dosha(
            symptoms=patient_info.symptoms,
            constitution_dosha=patient_info.constitution_dosha,
            diagnosis=patient_info.doctor_diagnosis,
            n_results=5
        )
        
        # Generate prescription and extract medications/lifestyle
        logger.info("Generating medication and lifestyle recommendations...")
        prescription_result = prescription_generator.generate_prescription(
            patient_info=patient_info,
            similar_cases=similar_cases,
            output_format="json"
        )
        
        if prescription_result["success"]:
            json_data = prescription_result.get("json_format", {})
            prescription_data = json_data.get("prescription", {})
            
            return MedicationResponse(
                success=True,
                patient_info={
                    "name": patient_info.name,
                    "age": patient_info.age,
                    "gender": patient_info.gender,
                    "constitution_dosha": patient_info.constitution_dosha,
                    "symptoms": patient_info.symptoms,
                    "doctor_diagnosis": patient_info.doctor_diagnosis
                },
                ayurvedic_medicines=prescription_data.get("ayurvedic_medicines", []),
                lifestyle_recommendations=prescription_data.get("lifestyle_recommendations", []),
                similar_cases_count=prescription_result.get("similar_cases_count", 0)
            )
        else:
            return MedicationResponse(
                success=False,
                error_message="Failed to generate medication recommendations"
            )
        
    except Exception as e:
        logger.error(f"Error generating medication recommendations: {e}")
        return MedicationResponse(
            success=False,
            error_message=str(e)
        )


@app.post("/generate-diet", response_model=DietResponse)
async def generate_diet_recommendations(patient_request: PatientRequest):
    """
    Generate Ayurvedic diet recommendations and meal chart
    """
    try:
        if not rag_processor or not prescription_generator:
            raise HTTPException(
                status_code=500,
                detail="System not properly initialized"
            )
        
        # Convert request to PatientInfo
        patient_info = PatientInfo(
            name=patient_request.name,
            age=patient_request.age,
            gender=patient_request.gender,
            constitution_dosha=patient_request.constitution_dosha,
            symptoms=patient_request.symptoms,
            doctor_diagnosis=patient_request.doctor_diagnosis
        )
        
        # Search for similar cases
        logger.info(
            f"Searching for diet recommendations for: {patient_info.name}"
        )
        similar_cases = rag_processor.search_by_symptoms_and_dosha(
            symptoms=patient_info.symptoms,
            constitution_dosha=patient_info.constitution_dosha,
            diagnosis=patient_info.doctor_diagnosis,
            n_results=5
        )
        
        # Generate prescription and extract diet recommendations
        logger.info("Generating diet recommendations...")
        prescription_result = prescription_generator.generate_prescription(
            patient_info=patient_info,
            similar_cases=similar_cases,
            output_format="json"
        )
        
        if prescription_result["success"]:
            json_data = prescription_result.get("json_format", {})
            prescription_data = json_data.get("prescription", {})
            diet_recs = prescription_data.get("diet_recommendations", {})
            
            # Create formatted diet chart
            diet_chart = f"""+-----------+----------------------------------------+
| Meal      | Recommendation                         |
+-----------+----------------------------------------+
| Breakfast | {diet_recs.get('breakfast', 'Not specified'):<38} |
| Lunch     | {diet_recs.get('lunch', 'Not specified'):<38} |
| Dinner    | {diet_recs.get('dinner', 'Not specified'):<38} |
| Drinks    | {diet_recs.get('drinks', 'Not specified'):<38} |
+-----------+----------------------------------------+"""
            
            return DietResponse(
                success=True,
                patient_info={
                    "name": patient_info.name,
                    "age": patient_info.age,
                    "gender": patient_info.gender,
                    "constitution_dosha": patient_info.constitution_dosha,
                    "symptoms": patient_info.symptoms,
                    "doctor_diagnosis": patient_info.doctor_diagnosis
                },
                diet_recommendations=diet_recs,
                diet_chart=diet_chart.strip(),
                similar_cases_count=prescription_result.get("similar_cases_count", 0)
            )
        else:
            return DietResponse(
                success=False,
                error_message="Failed to generate diet recommendations"
            )
        
    except Exception as e:
        logger.error(f"Error generating diet recommendations: {e}")
        return DietResponse(
            success=False,
            error_message=str(e)
        )


@app.post("/search-cases")
async def search_similar_cases(query: dict):
    """
    Search for similar cases in the knowledge base
    """
    try:
        if not rag_processor:
            raise HTTPException(
                status_code=500,
                detail="RAG processor not initialized"
            )
        
        search_query = query.get("query", "")
        n_results = query.get("n_results", 5)
        
        if not search_query:
            raise HTTPException(
                status_code=400,
                detail="Query parameter is required"
            )
        
        # Search for similar cases
        similar_cases = rag_processor.search_similar_cases(
            query=search_query,
            n_results=n_results
        )
        
        return {
            "success": True,
            "query": search_query,
            "results_count": len(similar_cases),
            "similar_cases": similar_cases
        }
        
    except Exception as e:
        logger.error(f"Error searching cases: {e}")
        return {
            "success": False,
            "error_message": str(e)
        }


@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        if not rag_processor:
            raise HTTPException(
                status_code=500,
                detail="RAG processor not initialized"
            )
        
        stats = rag_processor.get_collection_stats()
        
        return {
            "success": True,
            "system_stats": stats,
            "endpoints_available": {
                "generate_prescription": "/generate-prescription",
                "search_cases": "/search-cases",
                "health": "/health",
                "stats": "/stats"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "success": False,
            "error_message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )