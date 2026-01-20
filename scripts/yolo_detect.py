import os
import pandas as pd
import cv2
from ultralytics import YOLO
from pathlib import Path

def detect_and_classify():
    # Load YOLOv8 Nano model
    model = YOLO('yolov8n.pt')

    # Path setup
    raw_images_dir = Path('data/raw/images')
    # Save to dbt seeds directory for easy loading
    processed_dir = Path('medical_warehouse/seeds')
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    detections = []

    # Define product indicators
    product_objects = {'bottle', 'container', 'box', 'package'}

    # Recursive scan of images
    image_paths = list(raw_images_dir.rglob('*.jpg'))
    
    if not image_paths:
        print("No images found in data/raw/images")
        return

    for img_path in image_paths:
        channel_name = img_path.parent.name
        image_name = img_path.name
        message_id = img_path.stem  # Assuming filename is message_id
        
        # Run inference
        results = model(str(img_path))
        
        has_person = False
        has_product = False
        
        image_detections = []
        
        for result in results:
            for box in result.boxes:
                label = model.names[int(box.cls)]
                confidence = float(box.conf)
                
                if label == 'person':
                    has_person = True
                if label in product_objects:
                    has_product = True
                
                image_detections.append({
                    'image_name': image_name,
                    'message_id': message_id,
                    'channel_name': channel_name,
                    'detected_object': label,
                    'confidence_score': confidence
                })
        
        # Determine image category
        if has_person and has_product:
            category = 'promotional'
        elif has_product:
            category = 'product_display'
        elif has_person:
            category = 'lifestyle'
        else:
            category = 'other'
            
        # Add category to each detection for this image
        for det in image_detections:
            det['image_category'] = category
            detections.append(det)
        
        # If no objects were detected, we still want to record the image category
        if not image_detections:
            detections.append({
                'image_name': image_name,
                'message_id': message_id,
                'channel_name': channel_name,
                'detected_object': 'none',
                'confidence_score': 0.0,
                'image_category': category
            })

    # Save to CSV
    df = pd.DataFrame(detections)
    output_path = processed_dir / 'yolo_detections.csv'
    df.to_csv(output_path, index=False)
    print(f"Detections saved to {output_path}")

if __name__ == "__main__":
    detect_and_classify()
