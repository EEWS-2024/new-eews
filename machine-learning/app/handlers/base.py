from abc import ABC, abstractmethod
from typing import List, Dict, Any
import warnings
warnings.filterwarnings("ignore")

class BasePredictionHandler(ABC):
    """Abstract base class for prediction handlers"""
    
    @abstractmethod
    def predict(self, x: List[float], start_time: str, station_code: str) -> Dict[str, Any]:
        """Main prediction method for P and S wave detection"""
        pass
    
    @abstractmethod
    def predict_stats(self, x: List[float], station_code: str) -> Dict[str, Any]:
        """Predict earthquake statistics (magnitude, distance, etc.)"""
        pass 