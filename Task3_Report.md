# Task 3 Report: Image Data Enrichment

## Objective

The goal of this task was to analyze images scraped from medical Telegram channels using YOLOv8, classify them, and integrate the findings into the data warehouse for further analysis.

## Key Findings

### 1. Engagement Analysis

| Image Category                 | Average View Count |
| ------------------------------ | ------------------ |
| Lifestyle (Person only)        | 7,593              |
| Promotional (Person + Product) | 2,729              |
| Other                          | 1,426              |
| Product Display (Product only) | 721                |

**Insight**: Human presence significantly drives engagement. Images showing only products have the lowest engagement, while "lifestyle" content (people without explicit products) performs best. Promotional content (people with products) performs better than pure product displays but worse than pure lifestyle content.

### 2. Channel Behavior

| Channel Name      | Image Count |
| ----------------- | ----------- |
| lobelia4cosmetics | 200         |
| CheMed123         | 67          |
| tikvahpharma      | 64          |

**Insight**: `lobelia4cosmetics` is the most visually active channel in the dataset, posting significantly more images than the other channels combined.

## Model Limitations

Using a pre-trained YOLOv8 model for medical product detection has several limitations:

- **No Brand Recognition**: The model can identify a "bottle" or "box" but cannot distinguish between different medical brands or specific products like "Amoxicillin" vs "Ibuprofen".
- **Misclassification Risks**: Generic shapes like medical containers might be misclassified as "bottles" or "vases" if they don't exactly match the COCO dataset's "bottle" category.
- **Limited Context**: The model doesn't understand the _medical_ context. A person holding a box is "promotional" by our logic, but they could just be moving boxes in a warehouse.
- **Confidence Uncertainty**: Low confidence scores for small medical items can lead to noisy data in the warehouse.

## Deliverables

- `scripts/yolo_detect.py`: Object detection and classification script.
- `medical_warehouse/seeds/yolo_detections.csv`: Processed image detections.
- `medical_warehouse/models/marts/fct_image_detections.sql`: dbt fact table model.
- Integrated PostgreSQL table: `public.fct_image_detections`.
