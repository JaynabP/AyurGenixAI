import pandas as pd
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AyurvedicRAGProcessor:
    """Simplified RAG processor using text-based search"""
    
    def __init__(self, csv_path: str):
        """Initialize the RAG processor with text search"""
        self.csv_path = csv_path
        self.data = None
        self.load_data()
        logger.info(f"RAG processor initialized with {len(self.data)} records")
    
    def load_data(self):
        """Load the CSV data"""
        try:
            self.data = pd.read_csv(self.csv_path)
            logger.info(f"Successfully loaded {len(self.data)} records")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def search_by_symptoms_and_dosha(self, symptoms: List[str], 
                                   constitution_dosha: str,
                                   diagnosis: str = "",
                                   n_results: int = 5) -> List[Dict]:
        """
        Search for similar cases using text matching
        
        Args:
            symptoms: List of patient symptoms
            constitution_dosha: Patient's dosha constitution
            diagnosis: Doctor's diagnosis
            n_results: Number of results to return
            
        Returns:
            List of similar cases with metadata
        """
        try:
            if self.data is None:
                self.load_data()
            
            # Convert search terms to lowercase for matching
            symptoms_lower = [s.lower() for s in symptoms]
            dosha_lower = constitution_dosha.lower()
            diagnosis_lower = diagnosis.lower() if diagnosis else ""
            
            # Calculate relevance scores
            scores = []
            
            for idx, row in self.data.iterrows():
                score = 0
                
                # Check constitution match (high weight)
                if pd.notna(row.get('Constitution')) and dosha_lower in row['Constitution'].lower():
                    score += 10
                
                # Check disease/diagnosis match (high weight)
                if pd.notna(row.get('Disease')) and diagnosis_lower:
                    if diagnosis_lower in row['Disease'].lower() or row['Disease'].lower() in diagnosis_lower:
                        score += 8
                
                # Check symptoms match (medium weight)
                symptoms_text = str(row.get('Symptoms', ''))
                for symptom in symptoms_lower:
                    if symptom in symptoms_text.lower():
                        score += 3
                
                # Check herbs and formulations (low weight for context)
                herbs_text = str(row.get('Ayurvedic_Herbs', ''))
                formulation_text = str(row.get('Formulation', ''))
                
                for symptom in symptoms_lower:
                    if symptom in herbs_text.lower():
                        score += 1
                    if symptom in formulation_text.lower():
                        score += 1
                
                scores.append((score, idx))
            
            # Sort by score and get top results
            scores.sort(reverse=True, key=lambda x: x[0])
            top_indices = [idx for score, idx in scores[:n_results] if score > 0]
            
            # If no good matches, get some random samples
            if not top_indices:
                top_indices = self.data.head(n_results).index.tolist()
            
            # Format results
            results = []
            for idx in top_indices:
                row = self.data.iloc[idx]
                
                result = {
                    'id': str(idx),
                    'text': self._format_case_text(row),
                    'metadata': {
                        'disease': row.get('Disease', 'N/A'),
                        'symptoms': row.get('Symptoms', 'N/A'),
                        'constitution': row.get('Constitution', 'N/A'),
                        'ayurvedic_herbs': row.get('Ayurvedic_Herbs', 'N/A'),
                        'formulation': row.get('Formulation', 'N/A'),
                        'diet_recommendations': row.get('Diet_Recommendations', 'N/A'),
                        'lifestyle_recommendations': row.get('Lifestyle_Recommendations', 'N/A')
                    }
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} similar cases")
            return results
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
    
    def _format_case_text(self, row) -> str:
        """Format a case into readable text"""
        text_parts = []
        
        if pd.notna(row.get('Disease')):
            text_parts.append(f"Disease: {row['Disease']}")
        
        if pd.notna(row.get('Symptoms')):
            text_parts.append(f"Symptoms: {row['Symptoms']}")
        
        if pd.notna(row.get('Constitution')):
            text_parts.append(f"Constitution: {row['Constitution']}")
        
        if pd.notna(row.get('Ayurvedic_Herbs')):
            text_parts.append(f"Herbs: {row['Ayurvedic_Herbs']}")
        
        if pd.notna(row.get('Formulation')):
            text_parts.append(f"Formulation: {row['Formulation']}")
        
        return " | ".join(text_parts)
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        if self.data is None:
            return {"total_records": 0, "status": "not_loaded"}
        
        return {
            "total_records": len(self.data),
            "status": "loaded",
            "columns": list(self.data.columns),
            "constitution_types": self.data['Constitution'].value_counts().to_dict() if 'Constitution' in self.data.columns else {}
        }
    
    def search_by_text(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Simple text search across all fields
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of matching cases
        """
        try:
            if self.data is None:
                self.load_data()
            
            query_lower = query.lower()
            scores = []
            
            for idx, row in self.data.iterrows():
                score = 0
                
                # Search across all text fields
                for col in self.data.columns:
                    if pd.notna(row[col]):
                        text = str(row[col]).lower()
                        if query_lower in text:
                            score += text.count(query_lower)
                
                if score > 0:
                    scores.append((score, idx))
            
            # Sort by score and get top results
            scores.sort(reverse=True, key=lambda x: x[0])
            top_indices = [idx for score, idx in scores[:n_results]]
            
            results = []
            for idx in top_indices:
                row = self.data.iloc[idx]
                result = {
                    'id': str(idx),
                    'text': self._format_case_text(row),
                    'metadata': {
                        'disease': row.get('Disease', 'N/A'),
                        'symptoms': row.get('Symptoms', 'N/A'),
                        'constitution': row.get('Constitution', 'N/A'),
                        'ayurvedic_herbs': row.get('Ayurvedic_Herbs', 'N/A'),
                        'formulation': row.get('Formulation', 'N/A'),
                        'diet_recommendations': row.get('Diet_Recommendations', 'N/A')
                    }
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in text search: {e}")
            return []