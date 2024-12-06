import cv2
import numpy as np
from PIL import Image, ImageDraw
import os
from template_processor import TemplateProcessor

def create_sample_template():
    """Create a sample template with lines and rectangles"""
    # Create a white background
    template = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Draw horizontal lines for text
    cv2.line(template, (50, 100), (400, 100), (0, 0, 0), 2)  # Line 1
    cv2.line(template, (50, 200), (600, 200), (0, 0, 0), 2)  # Line 2
    
    # Draw rectangles for images
    cv2.rectangle(template, (50, 250), (250, 450), (0, 0, 0), 2)  # Rectangle 1
    cv2.rectangle(template, (300, 250), (500, 450), (0, 0, 0), 2)  # Rectangle 2
    
    return template

def create_sample_image(text: str, size=(200, 200), color=(200, 100, 100)):
    """Create a sample image with specified text"""
    img = np.ones((size[1], size[0], 3), dtype=np.uint8)
    img[:] = color
    
    # Add text to image
    cv2.putText(img, text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return img

def main():
    # Create output directory
    output_dir = "template_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create and save sample template
    template = create_sample_template()
    template_path = os.path.join(output_dir, "template.jpg")
    cv2.imwrite(template_path, template)
    
    # Create sample images
    img1 = create_sample_image("Image 1", color=(200, 100, 100))
    img2 = create_sample_image("Image 2", color=(100, 200, 100))
    
    img1_path = os.path.join(output_dir, "image1.jpg")
    img2_path = os.path.join(output_dir, "image2.jpg")
    cv2.imwrite(img1_path, img1)
    cv2.imwrite(img2_path, img2)
    
    # Initialize template processor
    processor = TemplateProcessor(template_path)
    
    # Detect regions
    processor.detect_regions()
    
    # Save debug visualizations
    processor.visualize_detection(output_dir)
    
    # Print detected regions
    regions = processor.get_region_info()
    print("\nDetected Regions:")
    for name, type_, (x, y, w, h) in regions:
        print(f"{name} ({type_}): x={x}, y={y}, width={w}, height={h}")
    
    # Overlay content
    processor.overlay_content(
        os.path.join(output_dir, "final_output.jpg"),
        text_content={
            'text_region_0': 'This is the first line of text',
            'text_region_1': 'This is the second line of text'
        },
        image_paths={
            'image_region_0': img1_path,
            'image_region_1': img2_path
        }
    )

if __name__ == "__main__":
    main()
