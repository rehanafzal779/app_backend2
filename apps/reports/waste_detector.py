"""
Waste Detection Service via external inference API.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_class_name(detection: Dict) -> str:
    return (
        detection.get('class_name')
        or detection.get('label')
        or detection.get('name')
        or detection.get('class')
        or 'Unknown'
    )


def _normalize_bbox(detection: Dict) -> Optional[Dict[str, float]]:
    bbox = detection.get('bbox')

    if isinstance(bbox, dict) and all(k in bbox for k in ('x1', 'y1', 'x2', 'y2')):
        return {
            'x1': _to_float(bbox.get('x1')),
            'y1': _to_float(bbox.get('y1')),
            'x2': _to_float(bbox.get('x2')),
            'y2': _to_float(bbox.get('y2')),
        }

    if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
        x, y, w, h = bbox
        x = _to_float(x)
        y = _to_float(y)
        w = _to_float(w)
        h = _to_float(h)
        return {
            'x1': x,
            'y1': y,
            'x2': x + w,
            'y2': y + h,
        }

    if all(k in detection for k in ('x1', 'y1', 'x2', 'y2')):
        return {
            'x1': _to_float(detection.get('x1')),
            'y1': _to_float(detection.get('y1')),
            'x2': _to_float(detection.get('x2')),
            'y2': _to_float(detection.get('y2')),
        }

    return None


def _detect_waste_via_api(image_file) -> Dict[str, any]:
    from django.conf import settings

    api_url = str(getattr(settings, 'WASTE_INFERENCE_API_URL', '') or '').strip()
    timeout = int(getattr(settings, 'WASTE_INFERENCE_TIMEOUT', 45))

    if not api_url:
        return {
            'ai_result': 'Unverified',
            'waste_type': None,
            'ai_confidence': 0.0,
            'detections': [],
            'valid_detections': [],
            'error': 'WASTE_INFERENCE_API_URL is not configured',
        }

    try:
        if hasattr(image_file, 'seek'):
            image_file.seek(0)

        file_name = getattr(image_file, 'name', 'image.jpg')
        file_bytes = image_file.read() if hasattr(image_file, 'read') else b''

        if hasattr(image_file, 'seek'):
            image_file.seek(0)

        if not file_bytes:
            return {
                'ai_result': 'Unverified',
                'waste_type': None,
                'ai_confidence': 0.0,
                'detections': [],
                'valid_detections': [],
                'error': 'Empty image file',
            }

        boundary = f'----NeatNowBoundary{uuid4().hex}'
        body = b''.join([
            f'--{boundary}\r\n'.encode('utf-8'),
            f'Content-Disposition: form-data; name="image"; filename="{os.path.basename(file_name)}"\r\n'.encode('utf-8'),
            b'Content-Type: application/octet-stream\r\n\r\n',
            file_bytes,
            b'\r\n',
            f'--{boundary}--\r\n'.encode('utf-8'),
        ])

        request = urllib.request.Request(
            api_url,
            data=body,
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Accept': 'application/json',
            },
            method='POST',
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode('utf-8'))

        api_status = str(payload.get('status', '')).lower()
        if api_status and api_status != 'success':
            return {
                'ai_result': 'Unverified',
                'waste_type': None,
                'ai_confidence': 0.0,
                'detections': [],
                'valid_detections': [],
                'error': payload.get('error') or payload.get('message') or 'Inference API returned failure status',
            }

        raw_detections = payload.get('detections') or []
        if not isinstance(raw_detections, list):
            raw_detections = []

        normalized_detections = []
        max_confidence = 0.0
        top_class_name = None

        for item in raw_detections:
            if not isinstance(item, dict):
                continue

            class_name = _extract_class_name(item)
            confidence = _to_float(item.get('confidence'))
            bbox = _normalize_bbox(item)

            normalized_item = {
                'class': class_name,
                'confidence': confidence,
                'class_id': item.get('class_id'),
            }
            if bbox:
                normalized_item['bbox'] = bbox

            normalized_detections.append(normalized_item)

            if confidence > max_confidence:
                max_confidence = confidence
                top_class_name = class_name

        if normalized_detections:
            return {
                'ai_result': 'Waste',
                'waste_type': top_class_name,
                'ai_confidence': round(max_confidence, 2),
                'detections': normalized_detections,
                'valid_detections': normalized_detections,
                'annotated_image_base64': payload.get('annotated_image_base64'),
            }

        return {
            'ai_result': 'No Waste',
            'waste_type': None,
            'ai_confidence': 0.0,
            'detections': [],
            'valid_detections': [],
            'annotated_image_base64': payload.get('annotated_image_base64'),
        }

    except urllib.error.HTTPError as e:
        error_body = None
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            error_body = str(e)

        logger.error(f'Inference API HTTP error ({e.code}): {error_body}')
        return {
            'ai_result': 'Unverified',
            'waste_type': None,
            'ai_confidence': 0.0,
            'detections': [],
            'valid_detections': [],
            'error': f'Inference API HTTP {e.code}',
        }
    except urllib.error.URLError as e:
        logger.error(f'Inference API connection error: {str(e)}')
        return {
            'ai_result': 'Unverified',
            'waste_type': None,
            'ai_confidence': 0.0,
            'detections': [],
            'valid_detections': [],
            'error': f'Inference API unavailable: {str(e)}',
        }
    except Exception as e:
        logger.error(f'Inference API parsing error: {str(e)}', exc_info=True)
        return {
            'ai_result': 'Unverified',
            'waste_type': None,
            'ai_confidence': 0.0,
            'detections': [],
            'valid_detections': [],
            'error': f'Inference API error: {str(e)}',
        }


def detect_waste(image_file) -> Dict[str, any]:
    return _detect_waste_via_api(image_file)


def reset_model():
    """Kept for backward compatibility; local model execution was removed."""
    return None
