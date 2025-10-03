import google.generativeai as genai
from typing import Dict, List
import logging
import json
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PatientInfo:
    """Patient information structure"""
    name: str
    age: int
    gender: str
    constitution_dosha: str
    symptoms: List[str]
    doctor_diagnosis: str


class EnhancedPrescriptionGenerator:
    def __init__(self, api_key: str):
        """Initialize with Gemini API"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.0-flash')

    def generate_prescription(self, patient_info: PatientInfo, 
                            similar_cases: List[Dict],
                            output_format: str = "display") -> Dict:
        """
        Generate precise Ayurvedic prescription
        
        Args:
            patient_info: Patient details
            similar_cases: RAG search results
            output_format: "display" or "json"
        """
        try:
            # Create focused prompt for exact format
            prompt = self._create_precise_prompt(patient_info, similar_cases)
            
            # Generate with Gemini
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Create both formats
                display_text = self._format_display_output(response.text, patient_info)
                json_output = self._create_json_output(response.text, patient_info)
                
                return {
                    "success": True,
                    "display_format": display_text,
                    "json_format": json_output,
                    "raw_response": response.text,
                    "similar_cases_count": len(similar_cases)
                }
            else:
                return self._create_fallback_response(patient_info)
                
        except Exception as e:
            logger.error(f"Error generating prescription: {e}")
            return self._create_fallback_response(patient_info)

    def _create_precise_prompt(self, patient_info: PatientInfo, 
                             similar_cases: List[Dict]) -> str:
        """Create focused prompt for exact format matching"""
        
        # Patient info
        patient_section = f"""
PATIENT: {patient_info.name}, {patient_info.age} years, {patient_info.gender}
CONSTITUTION: {patient_info.constitution_dosha}
SYMPTOMS: {', '.join(patient_info.symptoms)}
DIAGNOSIS: {patient_info.doctor_diagnosis}
"""

        # Similar cases context
        context_section = "SIMILAR SUCCESSFUL CASES:\n"
        for i, case in enumerate(similar_cases[:3], 1):
            metadata = case.get('metadata', {})
            context_section += f"""
Case {i}: {metadata.get('disease', 'N/A')}
- Constitution: {metadata.get('constitution', 'N/A')}
- Herbs used: {metadata.get('ayurvedic_herbs', 'N/A')}
- Formulation: {metadata.get('formulation', 'N/A')}
- Diet advice: {metadata.get('diet_recommendations', 'N/A')}
"""

        # Main prompt
        prompt = f"""
You are an expert Ayurvedic doctor. Based on the patient information and similar cases, 
create a prescription in EXACTLY this format:

{patient_section}

{context_section}

Generate a prescription following this EXACT structure and format:

Prescription for [Name] ([Age], [Gender], [Constitution] constitution):

1. Ayurvedic Medicines:
   • [Medicine 1]: [dosage and timing]
   • [Medicine 2]: [dosage and timing]  
   • [Medicine 3]: [dosage and timing]

2. Diet Recommendation:
   +-----------+----------------------------------------+
   | Meal      | Recommendation                         |
   +-----------+----------------------------------------+
   | Breakfast | [specific breakfast recommendations]    |
   | Lunch     | [specific lunch recommendations]       |
   | Dinner    | [specific dinner recommendations]      |
   | Drinks    | [recommended beverages]                |
   +-----------+----------------------------------------+

3. Lifestyle Recommendations:
   • [Specific practice 1 with duration]
   • [Specific practice 2 with duration]
   • [Specific practice 3 with timing]
   • [Specific dietary restriction]
   • [Specific stress management with duration]

Requirements:
- Use authentic Ayurvedic medicines appropriate for the constitution and symptoms
- Keep recommendations practical and specific
- Include precise dosages and timings
- Focus on the patient's Pitta/Vata/Kapha constitution
- Make it suitable for modern lifestyle
- Keep the exact formatting with bullet points (•) and table structure
"""
        
        return prompt

    def _format_display_output(self, response_text: str, patient_info: PatientInfo) -> str:
        """Format for beautiful display output"""
        
        header = f"""
{'═'*80}
                    AYURVEDIC PRESCRIPTION
{'═'*80}
Patient: {patient_info.name} | Age: {patient_info.age} | Gender: {patient_info.gender}
Constitution: {patient_info.constitution_dosha}
Diagnosis: {patient_info.doctor_diagnosis}
Symptoms: {', '.join(patient_info.symptoms)}
Date: {datetime.now().strftime("%B %d, %Y")}
{'═'*80}

"""
        
        footer = f"""

{'═'*80}
                        IMPORTANT NOTES
{'═'*80}
• Follow the prescription consistently for optimal results
• Maintain regular meal times and sleep schedule  
• Stay hydrated with warm water throughout the day
• Consult an Ayurvedic physician if symptoms persist
• This prescription is based on traditional Ayurvedic principles

Generated by AyurGenixAI - Your Ayurvedic Health Companion
{'═'*80}
"""
        
        return header + response_text + footer

    def _create_json_output(self, response_text: str, patient_info: PatientInfo) -> Dict:
        """Create structured JSON output"""
        
        # Parse the response to extract structured data
        try:
            # Extract medicines (simplified parsing)
            medicines = []
            diet_recommendations = {}
            lifestyle_recommendations = []
            
            lines = response_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if "1. Ayurvedic Medicines:" in line:
                    current_section = "medicines"
                elif "2. Diet Recommendation:" in line:
                    current_section = "diet"
                elif "3. Lifestyle Recommendations:" in line:
                    current_section = "lifestyle"
                elif line.startswith('•') and current_section == "medicines":
                    medicines.append(line[1:].strip())
                elif line.startswith('•') and current_section == "lifestyle":
                    lifestyle_recommendations.append(line[1:].strip())
                elif '|' in line and current_section == "diet":
                    if 'Breakfast' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            diet_recommendations['breakfast'] = parts[2].strip()
                    elif 'Lunch' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            diet_recommendations['lunch'] = parts[2].strip()
                    elif 'Dinner' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            diet_recommendations['dinner'] = parts[2].strip()
                    elif 'Drinks' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            diet_recommendations['drinks'] = parts[2].strip()
            
            # Create structured JSON
            prescription_json = {
                "patient_info": {
                    "name": patient_info.name,
                    "age": patient_info.age,
                    "gender": patient_info.gender,
                    "constitution": patient_info.constitution_dosha,
                    "diagnosis": patient_info.doctor_diagnosis,
                    "symptoms": patient_info.symptoms
                },
                "prescription": {
                    "ayurvedic_medicines": medicines,
                    "diet_recommendations": diet_recommendations,
                    "lifestyle_recommendations": lifestyle_recommendations
                },
                "metadata": {
                    "generated_date": datetime.now().isoformat(),
                    "generated_by": "AyurGenixAI",
                    "format_version": "1.0"
                }
            }
            
            return prescription_json
            
        except Exception as e:
            logger.error(f"Error creating JSON output: {e}")
            # Fallback JSON structure
            return {
                "patient_info": {
                    "name": patient_info.name,
                    "age": patient_info.age,
                    "gender": patient_info.gender,
                    "constitution": patient_info.constitution_dosha,
                    "diagnosis": patient_info.doctor_diagnosis,
                    "symptoms": patient_info.symptoms
                },
                "prescription": {
                    "raw_text": response_text
                },
                "metadata": {
                    "generated_date": datetime.now().isoformat(),
                    "generated_by": "AyurGenixAI",
                    "format_version": "1.0",
                    "parsing_error": str(e)
                }
            }

    def _create_fallback_response(self, patient_info: PatientInfo) -> Dict:
        """Create fallback response if AI fails"""
        
        fallback_text = f"""
Prescription for {patient_info.name} ({patient_info.age}, {patient_info.gender}, {patient_info.constitution_dosha} constitution):

1. Ayurvedic Medicines:
   • Triphala Churna: 1 tsp with warm water at bedtime
   • Ashwagandha powder: 1/2 tsp with warm milk twice daily
   • Amla juice: 20 ml with water in the morning

2. Diet Recommendation:
   +-----------+----------------------------------------+
   | Meal      | Recommendation                         |
   +-----------+----------------------------------------+
   | Breakfast | Warm oats with seasonal fruits         |
   | Lunch     | Rice with dal and cooked vegetables    |
   | Dinner    | Light khichdi or vegetable soup        |
   | Drinks    | Warm water, herbal teas                |
   +-----------+----------------------------------------+

3. Lifestyle Recommendations:
   • Practice Anulom-Vilom pranayama daily (10 minutes)
   • Morning walk for 20-30 minutes
   • Sleep by 10 PM, wake by 6 AM
   • Avoid processed and cold foods
   • Practice meditation for stress relief (10 minutes daily)
"""
        
        display_format = self._format_display_output(fallback_text, patient_info)
        json_format = self._create_json_output(fallback_text, patient_info)
        
        return {
            "success": False,
            "display_format": display_format,
            "json_format": json_format,
            "error": "Using fallback prescription",
            "similar_cases_count": 0
        }