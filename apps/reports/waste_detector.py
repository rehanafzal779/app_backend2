"""
Waste Detection Service using YOLOv8
Handles ML model loading and inference for waste detection
"""
import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Global model instance (lazy loading)
_model_instance = None


def get_model_path() -> Path:
    """
    Get the path to the trained YOLOv8 model
    Returns path to .pt file or folder
    """
    from django.conf import settings
    
    # Try to get from settings, otherwise use default
    model_path = getattr(settings, 'WASTE_MODEL_PATH', None)
    
    if model_path:
        path = Path(model_path)
        if path.exists():
            return path
    
    # Default path relative to BASE_DIR
    base_dir = Path(settings.BASE_DIR)
    model_ml_dir = base_dir / 'model_ml'
    
    # Check for .pt file in model_ml directory
    pt_file = model_ml_dir / 'best.pt'
    if pt_file.exists():
        return pt_file
    
    # Check for .pt file in best subdirectory
    pt_file_sub = model_ml_dir / 'best' / 'best.pt'
    if pt_file_sub.exists():
        return pt_file_sub
    
    # Check if best folder exists (PyTorch saved model format)
    best_folder = model_ml_dir / 'best'
    if best_folder.exists() and best_folder.is_dir():
        # Check if it contains data.pkl (PyTorch format)
        if (best_folder / 'data.pkl').exists():
            logger.warning("Found PyTorch folder format. YOLOv8 typically uses .pt files.")
            logger.warning("Please ensure you have best.pt file, or convert the model.")
            # Try to use folder anyway (may not work with YOLO)
            return best_folder
    
    # Fallback: return best folder path (will fail if doesn't exist)
    return best_folder


def load_model():
    """
    Load YOLOv8 model (lazy loading - only loads once)
    """
    global _model_instance
    
    if _model_instance is not None:
        return _model_instance
    
    try:
        from ultralytics import YOLO
        
        model_path = get_model_path()
        
        logger.info(f"📦 Loading waste detection model from: {model_path}")
        
        # Verify model file exists
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        # Check if it's a .pt file
        if model_path.is_file() and not str(model_path).endswith('.pt'):
            logger.warning(f"⚠️ Model path is not a .pt file: {model_path}")
        
        # Load model
        _model_instance = YOLO(str(model_path))
        
        # Verify model loaded correctly
        if _model_instance is None:
            raise RuntimeError("Model failed to load - YOLO returned None")
        
        # Set to evaluation mode
        if hasattr(_model_instance, 'model'):
            _model_instance.model.eval()
        
        # Log model info
        if hasattr(_model_instance, 'names'):
            class_count = len(_model_instance.names)
            logger.info(f"✅ Model loaded successfully with {class_count} classes")
            logger.info(f"📋 Classes: {list(_model_instance.names.values())}")
        else:
            logger.info("✅ Model loaded successfully")
        
        return _model_instance
        
    except ImportError:
        logger.error("Ultralytics YOLO not installed. Please install: pip install ultralytics")
        raise ImportError("Ultralytics YOLO library is required. Install with: pip install ultralytics")
    except FileNotFoundError as e:
        logger.error(f"Model file not found: {model_path}")
        raise FileNotFoundError(
            f"Waste detection model not found at: {model_path}\n"
            f"Please ensure you have a 'best.pt' file in the model_ml directory."
        )
    except Exception as e:
        logger.error(f"Failed to load waste detection model from {model_path}: {str(e)}")
        raise RuntimeError(
            f"Failed to load waste detection model: {str(e)}\n"
            f"Model path: {model_path}\n"
            f"Please ensure the model file is a valid YOLOv8 .pt file."
        )


def detect_waste(image_file) -> Dict[str, any]:
    """
    Detect waste in uploaded image using YOLOv8 model
    
    Saves uploaded file temporarily for inference, then deletes it.
    
    Args:
        image_file: Django uploaded file or file path
        
    Returns:
        Dictionary with:
        - ai_result: 'Waste' or 'No Waste'
        - waste_type: Detected waste type (if waste found)
        - ai_confidence: Confidence score (0.0 to 1.0)
        - detections: List of all detections
    """
    temp_file_path = None
    
    try:
        # Load model (lazy loading)
        model = load_model()
        
        # Prepare temporary file for YOLO inference
        if hasattr(image_file, 'read'):
            # Django uploaded file - save to temporary file
            image_file.seek(0)  # Reset file pointer
            
            # Get file extension from uploaded file
            file_name = getattr(image_file, 'name', 'image.jpg')
            file_ext = os.path.splitext(file_name)[1] or '.jpg'
            
            # Create temporary file in temp directory
            from django.conf import settings
            temp_dir = settings.MEDIA_ROOT / 'temp'
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Create unique temporary file
            with tempfile.NamedTemporaryFile(
                dir=str(temp_dir),
                suffix=file_ext,
                delete=False
            ) as temp_file:
                # Write uploaded file content to temp file
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Reset file pointer for potential reuse
            image_file.seek(0)
            
            # Use temp file path for YOLO
            source = temp_file_path
            
        else:
            # Already a file path - use directly
            source = str(image_file)
        
        # Run inference on temporary file
        # Use higher initial threshold to reduce false positives
        results = model.predict(
            source=source,
            imgsz=640,
            conf=0.50,  # Initial detection threshold (50% minimum) - increased to reduce false positives
            verbose=False
        )
        
        # Minimum confidence to accept as "Waste" 
        # Different thresholds for different waste types
        # Animal Waste has lower model performance, so use lower threshold
        # Increased thresholds to reduce false positives
        DEFAULT_MIN_CONFIDENCE = 0.65  # 65% for most waste types (increased from 50%)
        ANIMAL_WASTE_MIN_CONFIDENCE = 0.50  # 50% for Animal Waste (increased from 35%)
        
        # Process results
        detections = []
        valid_detections = []  # Detections above minimum confidence
        max_confidence = 0.0
        detected_waste_type = None
        
        if results and len(results) > 0:
            result = results[0]
            
            # Get class names from model
            class_names = model.names if hasattr(model, 'names') else {}
            
            # Process detections
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    # Get class ID and confidence
                    cls_id = int(box.cls[0].item())
                    confidence = float(box.conf[0].item())
                    
                    # Get class name
                    class_name = class_names.get(cls_id, f"Class_{cls_id}")
                    
                    # Store all detections for logging
                    detections.append({
                        'class': class_name,
                        'confidence': confidence,
                        'class_id': cls_id
                    })
                    
                    # Determine threshold based on waste type
                    # Animal Waste needs lower threshold due to model's lower performance on this class
                    is_animal_waste = 'Animal' in class_name or 'animal' in class_name.lower()
                    min_confidence = ANIMAL_WASTE_MIN_CONFIDENCE if is_animal_waste else DEFAULT_MIN_CONFIDENCE
                    
                    # Log detection for debugging (especially Animal Waste)
                    if is_animal_waste:
                        logger.info(f"🐾 Animal Waste detection: {class_name} with confidence {confidence:.2f} (threshold: {min_confidence:.2f})")
                    else:
                        logger.debug(f"Detection: {class_name} with confidence {confidence:.2f}")
                    
                    # Only consider detections above minimum confidence threshold (class-specific)
                    if confidence >= min_confidence:
                        valid_detections.append({
                            'class': class_name,
                            'confidence': confidence,
                            'class_id': cls_id
                        })
                        
                        # Track highest confidence detection
                        if confidence > max_confidence:
                            max_confidence = confidence
                            detected_waste_type = class_name
                    else:
                        # Log low confidence detections (especially Animal Waste)
                        if is_animal_waste:
                            logger.warning(f"⚠️ Animal Waste detected but confidence too low: {confidence:.2f} < {min_confidence:.2f}")
                        else:
                            logger.debug(f"Low confidence detection rejected: {class_name} ({confidence:.2f} < {min_confidence:.2f})")
        
        # Log all detections for debugging
        if len(detections) > 0:
            logger.info(f"🔍 Detection Summary: Total={len(detections)}, Valid={len(valid_detections)}")
            logger.info(f"📊 Thresholds: Default={DEFAULT_MIN_CONFIDENCE:.2f}, Animal={ANIMAL_WASTE_MIN_CONFIDENCE:.2f}")
            for det in detections:
                is_animal = 'Animal' in det['class'] or 'animal' in det['class'].lower()
                threshold_used = ANIMAL_WASTE_MIN_CONFIDENCE if is_animal else DEFAULT_MIN_CONFIDENCE
                status = "✓ ACCEPTED" if det['confidence'] >= threshold_used else "✗ REJECTED"
                logger.info(f"  - {det['class']}: {det['confidence']:.2f} (threshold: {threshold_used:.2f}) {status}")
        else:
            logger.info("🔍 No detections found in image (model returned empty results)")
        
        # Determine result based on valid detections (above threshold)
        if len(valid_detections) > 0:
            # Waste detected with sufficient confidence
            logger.info(f"✅ Waste detected: {detected_waste_type} with confidence {max_confidence:.2f}")
            result = {
                'ai_result': 'Waste',
                'waste_type': detected_waste_type,
                'ai_confidence': round(max_confidence, 2),
                'detections': detections,  # All detections for debugging
                'valid_detections': valid_detections  # Only high-confidence detections
            }
        else:
            # No waste detected or confidence too low
            if len(detections) > 0:
                logger.warning(f"❌ No valid waste detected. Found {len(detections)} detections but all below threshold")
                # Check if Animal Waste was detected but rejected
                animal_detections = [d for d in detections if 'Animal' in d['class'] or 'animal' in d['class'].lower()]
                if animal_detections:
                    logger.warning(f"   Animal Waste was detected but confidence too low. Max confidence: {max([d['confidence'] for d in animal_detections]):.2f}")
            else:
                logger.info("No detections found in image")
            result = {
                'ai_result': 'No Waste',
                'waste_type': None,
                'ai_confidence': 0.0,
                'detections': detections,  # Log all detections for debugging
                'valid_detections': []
            }
        
        return result
            
    except Exception as e:
        logger.error(f"Error during waste detection: {str(e)}", exc_info=True)
        
        # Return safe default on error
        return {
            'ai_result': 'Unverified',
            'waste_type': None,
            'ai_confidence': 0.0,
            'detections': [],
            'error': str(e)
        }
    
    finally:
        # Always delete temporary file after inference
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Deleted temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {str(e)}")


def reset_model():
    """
    Reset model instance (useful for testing or reloading)
    """
    global _model_instance
    _model_instance = None

