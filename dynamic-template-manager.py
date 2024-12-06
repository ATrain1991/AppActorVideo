from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import pytesseract

# Add this line for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@dataclass
class TemplateRegion:
    x1: int
    y1: int
    x2: int
    y2: int
    content_type: str  # 'image', 'text', or 'score'
    identifier: str    # e.g., 'poster_1', 'critic_score_1'

class TemplateManager:
    def __init__(self, template_path: str):
        """
        Initialize template manager with path to template image
        """
        self.template = cv2.imread(template_path)
        self.height, self.width = self.template.shape[:2]
        self.regions = self._analyze_template()

    def _analyze_template(self) -> List[TemplateRegion]:
        """
        Analyze template to detect regions automatically
        """
        regions = []
        
        # Convert to PIL Image for text detection
        pil_image = Image.fromarray(cv2.cvtColor(self.template, cv2.COLOR_BGR2RGB))
        
        # Detect text regions using pytesseract
        text_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
        
        # Process text regions
        for i in range(len(text_data['text'])):
            if text_data['conf'][i] > 0:  # Filter confident detections
                x = text_data['left'][i]
                y = text_data['top'][i]
                w = text_data['width'][i]
                h = text_data['height'][i]
                text = text_data['text'][i]
                
                # Categorize regions based on content
                if text.endswith('%'):
                    content_type = 'score'
                    identifier = f"score_{len([r for r in regions if r.content_type == 'score']) + 1}"
                else:
                    content_type = 'text'
                    identifier = f"text_{len([r for r in regions if r.content_type == 'text']) + 1}"
                
                regions.append(TemplateRegion(
                    x1=x, y1=y, x2=x+w, y2=y+h,
                    content_type=content_type,
                    identifier=identifier
                ))
        
        # Detect poster regions (large rectangular areas)
        gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            # Filter for poster-sized rectangles
            if w > self.width * 0.15 and h > self.height * 0.1:  # Adjust thresholds as needed
                regions.append(TemplateRegion(
                    x1=x, y1=y, x2=x+w, y2=y+h,
                    content_type='image',
                    identifier=f"poster_{len([r for r in regions if r.content_type == 'image']) + 1}"
                ))
        
        return regions

    def replace_content(self, region_identifier: str, new_content: any) -> bool:
        """
        Replace content in specified region
        new_content can be:
        - Path to image file for 'image' regions
        - String for 'text' or 'score' regions
        """
        matching_regions = [r for r in self.regions if r.identifier == region_identifier]
        if not matching_regions:
            return False
        
        region = matching_regions[0]
        if region.content_type == 'image':
            if isinstance(new_content, str):  # Assume it's a path to image file
                new_image = cv2.imread(new_content)
                if new_image is None:
                    return False
                # Resize to fit region
                new_image = cv2.resize(new_image, 
                                     (region.x2 - region.x1, region.y2 - region.y1))
                # Replace in template
                self.template[region.y1:region.y2, region.x1:region.x2] = new_image
                return True
        else:  # text or score
            if isinstance(new_content, (str, int, float)):
                # Create text image
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 2
                thickness = 2
                text = str(new_content)
                
                # Calculate text size and position
                (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                x = region.x1
                y = region.y1 + text_height
                
                # Clear region
                cv2.rectangle(self.template, 
                            (region.x1, region.y1), 
                            (region.x2, region.y2), 
                            (255, 255, 255), 
                            -1)
                
                # Add new text
                cv2.putText(self.template, text, (x, y), 
                           font, font_scale, (0, 0, 0), thickness)
                return True
        
        return False

    def save_template(self, output_path: str):
        """Save modified template to file"""
        cv2.imwrite(output_path, self.template)

    def get_region_info(self) -> Dict[str, TemplateRegion]:
        """Return dictionary of all regions and their properties"""
        return {region.identifier: region for region in self.regions}

def main():
    # Example usage
    template_manager = TemplateManager('template.jpg')
    
    # Print all detected regions
    regions = template_manager.get_region_info()
    for identifier, region in regions.items():
        print(f"Region {identifier}: {region}")
    
    # Example replacements
    template_manager.replace_content('poster_1', 'Aquaman.jpg')
    template_manager.replace_content('score_1', '95%')
    template_manager.replace_content('text_1', 'New Movie Title')
    
    # Save modified template
    template_manager.save_template('modified_template.jpg')

if __name__ == "__main__":
    main()
