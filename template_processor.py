import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from typing import List, Tuple, Optional
import os

@dataclass
class TemplateRegion:
    """Represents a region in the template where content can be overlaid"""
    x: int
    y: int
    width: int
    height: int
    type: str  # 'text' or 'image'
    name: str  # identifier for the region

class TemplateProcessor:
    def __init__(self, template_path: str):
        """Initialize with path to template image"""
        self.template = cv2.imread(template_path)
        self.gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        self.regions = []
        
    def visualize_detection(self, output_dir: str):
        """
        Save visualization images showing detected regions
        
        Args:
            output_dir: Directory to save visualization images
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Create copies for different visualizations
        text_vis = self.template.copy()
        image_vis = self.template.copy()
        combined_vis = self.template.copy()
        
        # Draw detected regions
        for region in self.regions:
            if region.type == 'text':
                # Draw text regions in blue
                cv2.rectangle(text_vis, 
                            (region.x, region.y),
                            (region.x + region.width, region.y + region.height),
                            (255, 0, 0), 2)
                cv2.putText(text_vis, region.name,
                          (region.x, region.y - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                
                # Add to combined visualization
                cv2.rectangle(combined_vis,
                            (region.x, region.y),
                            (region.x + region.width, region.y + region.height),
                            (255, 0, 0), 2)
                
            elif region.type == 'image':
                # Draw image regions in green
                cv2.rectangle(image_vis,
                            (region.x, region.y),
                            (region.x + region.width, region.y + region.height),
                            (0, 255, 0), 2)
                cv2.putText(image_vis, region.name,
                          (region.x, region.y - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Add to combined visualization
                cv2.rectangle(combined_vis,
                            (region.x, region.y),
                            (region.x + region.width, region.y + region.height),
                            (0, 255, 0), 2)
        
        # Save visualizations
        cv2.imwrite(os.path.join(output_dir, 'text_regions.jpg'), text_vis)
        cv2.imwrite(os.path.join(output_dir, 'image_regions.jpg'), image_vis)
        cv2.imwrite(os.path.join(output_dir, 'combined_regions.jpg'), combined_vis)
        
        # Save binary images used in detection
        _, binary = cv2.threshold(self.gray, 127, 255, cv2.THRESH_BINARY)
        cv2.imwrite(os.path.join(output_dir, 'binary.jpg'), binary)
        
        # Save horizontal line detection
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        detect_horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        cv2.imwrite(os.path.join(output_dir, 'horizontal_lines.jpg'), detect_horizontal)
    
    def detect_regions(self, 
                      min_line_length=50,
                      line_thickness_range=(1, 3),
                      rectangle_thickness_range=(1, 3)):
        """
        Detect regions in template:
        - Horizontal lines for text placement (text goes above the line)
        - Rectangle outlines for image placement
        """
        # Convert to binary image
        _, binary = cv2.threshold(self.gray, 127, 255, cv2.THRESH_BINARY)
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length, 1))
        detect_horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Find horizontal lines
        contours, _ = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process text regions (above horizontal lines)
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            if line_thickness_range[0] <= h <= line_thickness_range[1]:
                text_height = 30  # Approximate height for text
                self.regions.append(TemplateRegion(
                    x=x,
                    y=y - text_height,
                    width=w,
                    height=text_height,
                    type='text',
                    name=f'text_region_{i}'
                ))
        
        # Find rectangles (for image regions)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours):
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                contour_area = cv2.contourArea(contour)
                rect_area = w * h
                
                if contour_area < rect_area * 0.9:
                    mask = np.zeros_like(self.gray)
                    cv2.drawContours(mask, [contour], -1, (255), 1)
                    outline_pixels = cv2.countNonZero(mask)
                    perimeter = cv2.arcLength(contour, True)
                    thickness = outline_pixels / perimeter
                    
                    if rectangle_thickness_range[0] <= thickness <= rectangle_thickness_range[1]:
                        self.regions.append(TemplateRegion(
                            x=x,
                            y=y,
                            width=w,
                            height=h,
                            type='image',
                            name=f'image_region_{i}'
                        ))
    
    def overlay_content(self, output_path: str, 
                       text_content: dict = None, 
                       image_paths: dict = None):
        """Overlay text and images onto the template"""
        result = Image.fromarray(cv2.cvtColor(self.template, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(result)
        
        for region in self.regions:
            if region.type == 'text' and text_content and region.name in text_content:
                font = ImageFont.load_default()
                draw.text((region.x, region.y), 
                         text_content[region.name],
                         font=font,
                         fill=(0, 0, 0))
                
            elif region.type == 'image' and image_paths and region.name in image_paths:
                overlay = Image.open(image_paths[region.name])
                overlay = overlay.resize((region.width, region.height))
                result.paste(overlay, (region.x, region.y))
        
        result.save(output_path)

    def get_region_info(self) -> List[Tuple[str, str, Tuple[int, int, int, int]]]:
        """Return information about detected regions"""
        return [(r.name, r.type, (r.x, r.y, r.width, r.height)) 
                for r in self.regions]
