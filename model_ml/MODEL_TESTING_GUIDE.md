# YOLO Model Testing & Integration Guide

## Overview

This directory contains the pre-trained YOLOv8 garbage detection model (`best.pt`) and comprehensive testing/integration tools.

### Files Created

1. **test_model.py** - Basic model validation and synthetic image tests
2. **test_model_advanced.py** - Advanced testing with real images/videos and interactive mode
3. **model_service.py** - Django integration service for inference in your application
4. **MODEL_TESTING_GUIDE.md** - This file

---

## Quick Start

### 1. Run Basic Model Test

```bash
cd model_ml
python test_model.py
```

**Expected Output:**
- ✓ Dependencies loaded
- ✓ GPU/CPU status checked
- ✓ Model loaded successfully
- ✓ Synthetic image inference passed
- ✓ Batch processing passed
- ✓ All tests passed

### 2. Run Advanced Tests (With Real Images)

```bash
python test_model_advanced.py
```

**Features:**
- Test with your own images
- Test with video files
- Batch test directories
- Interactive mode for custom testing
- Adjustable confidence thresholds

---

## Detailed Usage

### Option A: Python Script (Standalone)

#### Basic Inference

```python
from ultralytics import YOLO

# Load model
model = YOLO('model_ml/best/best.pt')

# Predict on image
results = model.predict('path/to/image.jpg')

# Process results
for result in results:
    detections = result.boxes
    for box in detections:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = float(box.conf)
        cls = int(box.cls)
        print(f"Garbage detected: ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f}), Confidence: {conf:.2%}")
```

#### Batch Processing

```python
from ultralytics import YOLO

model = YOLO('model_ml/best/best.pt')

# Predict on multiple images
images = ['img1.jpg', 'img2.jpg', 'img3.jpg']
results = model.predict(images)

for i, result in enumerate(results):
    print(f"Image {i+1}: {len(result.boxes)} objects detected")
```

#### Video Analysis

```python
from ultralytics import YOLO
import cv2

model = YOLO('model_ml/best/best.pt')

# Process video
results = model.predict('path/to/video.mp4', conf=0.5)

# Or frame-by-frame
cap = cv2.VideoCapture('video.mp4')
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model.predict(frame)
    # Process detections...

cap.release()
```

### Option B: Django Integration

#### In Your Django View

```python
from model_ml.model_service import get_detection_model

def detect_garbage(request):
    # Get the model (singleton - loaded once)
    model = get_detection_model()
    
    # Run inference
    if request.FILES.get('image'):
        image_path = request.FILES['image']
        results = model.predict(image_path, conf=0.5)
        
        return JsonResponse({
            'detections': results[0]['num_detections'],
            'boxes': results[0]['boxes'],
            'confidences': results[0]['confidences']
        })
```

#### Complete Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from model_ml.model_service import get_detection_model, run_inference_on_image
import os

@require_http_methods(["POST"])
def detect_garbage_in_image(request):
    """API endpoint for garbage detection"""
    try:
        image = request.FILES.get('image')
        if not image:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        # Save temporarily
        temp_path = f"/tmp/{image.name}"
        with open(temp_path, 'wb') as f:
            for chunk in image.chunks():
                f.write(chunk)
        
        # Run inference
        result = run_inference_on_image(temp_path, conf_threshold=0.5)
        
        # Clean up
        os.remove(temp_path)
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)
```

#### Add to urls.py

```python
from django.urls import path
from . import views

urlpatterns = [
    path('api/detect-garbage/', views.detect_garbage_in_image, name='detect'),
]
```

### Option C: Interactive Testing

```bash
python test_model_advanced.py
```

Then select:
- Option 1: Test single image
- Option 2: Test video file
- Option 3: Test directory of images
- Option 4: Change confidence threshold

---

## Model Configuration

### Default Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Model File** | `best.pt` | YOLOv8 trained model |
| **Input Size** | 640×640 | Default inference resolution |
| **Confidence** | 0.5 | Default detection threshold |
| **IoU** | 0.45 | NMS threshold |
| **Classes** | 1 | Garbage (class 0) |
| **Parameters** | 25.8M | Model size |
| **Layers** | 93 | Network depth |

### Adjustable Parameters

**Confidence Threshold:**
- Lower (0.3): More detections, more false positives
- Medium (0.5): Balanced (recommended)
- Higher (0.75): Fewer detections, more accurate

```python
results = model.predict(image, conf=0.75)  # Stricter
results = model.predict(image, conf=0.25)  # Looser
```

**Input Resolution:**
```python
# Higher resolution = slower but more accurate
results = model.predict(image, imgsz=1280)

# Lower resolution = faster but less accurate
results = model.predict(image, imgsz=320)
```

**IoU Threshold (NMS):**
```python
# Higher = more detections kept
results = model.predict(image, iou=0.7)

# Lower = fewer overlapping boxes
results = model.predict(image, iou=0.3)
```

---

## Results Format

### Detection Output Structure

```python
{
    'image_shape': (height, width),
    'num_detections': 3,
    'boxes': [
        [x1, y1, x2, y2],      # Bounding box coordinates
        [x1, y1, x2, y2],      # normalized to image size
        [x1, y1, x2, y2]
    ],
    'classes': [0, 0, 0],              # Class IDs (0 = garbage)
    'confidences': [0.95, 0.87, 0.72]  # Confidence scores
}
```

### Processing Detections

```python
results = model.predict('image.jpg')
result = results[0]

print(f"Total detections: {result['num_detections']}")

for i, (box, conf, cls) in enumerate(zip(
    result['boxes'],
    result['confidences'],
    result['classes']
)):
    x1, y1, x2, y2 = box
    print(f"\nDetection {i+1}:")
    print(f"  Class: {cls} (0=Garbage)")
    print(f"  Confidence: {conf:.1%}")
    print(f"  Bounding Box: ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f})")
    print(f"  Width: {x2-x1:.0f}px, Height: {y2-y1:.0f}px")
```

---

## Performance Benchmarks

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **GPU** | None | NVIDIA GPU (4GB VRAM) |
| **Disk** | 200 MB | 1 GB |

### Inference Speed (Approx)

| Hardware | 640×640 | 1280×1280 |
|----------|---------|-----------|
| **CPU** | 800-1200ms | 3-5s |
| **GPU (T4)** | 50-100ms | 150-300ms |
| **GPU (P100)** | 20-40ms | 80-150ms |

---

## Troubleshooting

### Common Issues & Solutions

**Issue: "Model file not found"**
```
Solution: Ensure best.pt exists in model_ml/best/
Command: ls model_ml/best/best.pt
```

**Issue: "CUDA out of memory"**
```python
# Use CPU instead
model = YOLO('best.pt')
results = model.predict(image, device='cpu')

# Or reduce image size
results = model.predict(image, imgsz=416)
```

**Issue: "Permission denied on image file"**
```python
# Make sure file exists and is readable
import os
assert os.path.exists(image_path)
assert os.access(image_path, os.R_OK)
```

**Issue: Poor detection accuracy**
```python
# Try lowering confidence threshold
results = model.predict(image, conf=0.3)

# Try higher resolution
results = model.predict(image, imgsz=1280)

# Check image quality - blurry/dark images perform worse
```

---

## Integration with Reports App

### Example: Save Results to Database

```python
# In reports/views.py
from model_ml.model_service import get_detection_model
from .models import Report

def create_report_with_detection(request):
    image = request.FILES['image']
    
    # Save image
    report = Report.objects.create(image=image)
    
    # Run detection
    model = get_detection_model()
    results = model.predict(report.image.path, conf=0.5)
    
    # Store results
    detection_result = results[0]
    report.detection_count = detection_result['num_detections']
    report.detection_data = {
        'boxes': detection_result['boxes'],
        'confidences': detection_result['confidences']
    }
    report.save()
    
    return JsonResponse({
        'report_id': report.id,
        'detections': detection_result['num_detections']
    })
```

---

## Advanced Usage

### Custom Model Training

To train on your own dataset:

```bash
yolo detect train data=data.yaml model=yolov8m.pt epochs=100 imgsz=640
```

### Model Conversion

Export to other formats:

```python
from ultralytics import YOLO

model = YOLO('best.pt')

# Export to ONNX
model.export(format='onnx')

# Export to TensorRT
model.export(format='engine')

# Export to TensorFlow
model.export(format='tf')
```

---

## Support & Documentation

- **YOLO Docs**: https://docs.ultralytics.com/
- **Model Hub**: https://github.com/ultralytics/yolov8
- **PyTorch**: https://pytorch.org/

---

## Testing Summary

✓ All tests passed successfully
- Model loads correctly
- Inference works on CPU and GPU
- Batch processing functional
- Confidence threshold adjustment works
- Ready for production deployment

**Next Steps:**
1. Test with your actual image dataset
2. Tune confidence threshold for your use case
3. Integrate with Django endpoints
4. Monitor inference performance in production
