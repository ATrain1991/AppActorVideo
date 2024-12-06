from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageColor
import pytesseract
import os
from pathlib import Path
import colorsys
import re

# Add this line for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@dataclass
class TextStyle:
    font_family: str
    font_size: int
    color: Tuple[int, int, int]
    is_bold: bool
    is_italic: bool
    background_color: Optional[Tuple[int, int, int]] = None

@dataclass
class TemplateRegion:
    x1: int
    y1: int
    x2: int
    y2: int
    content_type: str  # 'image', 'text', or 'score'
    identifier: str    
    original_size: Tuple[int, int]
    text_style: Optional[TextStyle] = None

class TemplateManager:
    def __init__(self, template_path: str):
        """Initialize template manager with path to template image"""
        self.template_path = template_path
        self.template = cv2.imread(template_path)
        if self.template is None:
            raise ValueError(f"Could not load template image from {template_path}")
            
        self.height, self.width = self.template.shape[:2]
        self.pil_template = Image.fromarray(cv2.cvtColor(self.template, cv2.COLOR_BGR2RGB))
        self.draw = ImageDraw.Draw(self.pil_template)
        
        # Create visualization template
        self.viz_template = self.template.copy()
        
        # Common font paths by OS
        self.system_fonts = self._get_system_fonts()
        
        # Analyze template and store regions
        self.regions = self._analyze_template()
        
        # Draw initial region markers on visualization template
        self._update_visualization()

    def _get_system_fonts(self) -> Dict[str, str]:
        """Get system font paths based on OS"""
        font_paths = {}
        if os.name == 'nt':  # Windows
            font_dir = Path(os.environ['WINDIR']) / 'Fonts'
            common_fonts = {
                'arial': 'arial.ttf',
                'times': 'times.ttf',
                'calibri': 'calibri.ttf'
            }
        else:  # Unix-like
            font_dir = Path('/usr/share/fonts')
            common_fonts = {
                'arial': 'Arial.ttf',
                'times': 'Times.ttf',
                'calibri': 'Calibri.ttf'
            }
        
        for font_name, font_file in common_fonts.items():
            potential_path = font_dir / font_file
            if potential_path.exists():
                font_paths[font_name] = str(potential_path)
            
        return font_paths

    def _detect_text_style(self, region_img) -> TextStyle:
        """Detect text style including font, size, color, and attributes"""
        # Convert region to grayscale for OCR
        gray = cv2.cvtColor(region_img, cv2.COLOR_BGR2GRAY)
        
        # Get dominant color
        colors = cv2.mean(region_img)[:3]
        dominant_color = tuple(map(int, colors))
        
        # Get background color
        edges = cv2.Canny(gray, 50, 150)
        mask = cv2.dilate(edges, None)
        bg_colors = cv2.mean(region_img, mask=cv2.bitwise_not(mask))[:3]
        bg_color = tuple(map(int, bg_colors))
        
        # Detect if bold using pixel density
        is_bold = np.mean(gray) < 127
        
        # Detect if italic using edge analysis
        edges_sum = cv2.Sobel(gray, cv2.CV_64F, 1, 0).sum()
        is_italic = edges_sum > gray.size * 0.1
        
        # Estimate font size based on height
        font_size = region_img.shape[0]
        
        return TextStyle(
            font_family='arial',  # Default to arial, can be enhanced
            font_size=font_size,
            color=dominant_color,
            is_bold=is_bold,
            is_italic=is_italic,
            background_color=bg_color
        )

    def _analyze_template(self) -> List[TemplateRegion]:
        """Analyze template by detecting the structural grid from poster regions"""
        regions = []
        
        # Convert to HSV for color detection
        hsv = cv2.cvtColor(self.template, cv2.COLOR_BGR2HSV)
        
        # Detect red/orange rectangles
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        lower_orange = np.array([5, 100, 100])
        upper_orange = np.array([15, 255, 255])
        
        # Create masks and combine
        red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)
        color_mask = cv2.bitwise_or(cv2.bitwise_or(red_mask1, red_mask2), orange_mask)
        
        # Clean up mask
        kernel = np.ones((5,5), np.uint8)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find poster rectangles
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and sort rectangles by y-position
        poster_boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > self.width * 0.1 and h > self.height * 0.05:  # Filter small regions
                poster_boxes.append((y, x, y+h, x+w))
        
        poster_boxes.sort()  # Sort by y-coordinate
        
        if len(poster_boxes) < 1:
            print("Warning: No poster regions detected in template")
            return regions
            
        # Calculate row height - if only one poster, use a default
        row_height = (self.height // 5) if len(poster_boxes) < 2 else poster_boxes[1][0] - poster_boxes[0][0]
        
        # Create text style template
        text_style = TextStyle(
            font_family='arial',
            font_size=24,
            color=(0, 0, 0),
            is_bold=False,
            is_italic=False,
            background_color=(255, 255, 255)
        )
        
        # Add poster regions and calculate text regions
        for i, (y1, x1, y2, x2) in enumerate(poster_boxes):
            # Add poster region
            regions.append(TemplateRegion(
                x1=x1+2, y1=y1+2,
                x2=x2-2, y2=y2-2,
                content_type='image',
                identifier=f"poster_{i+1}",
                original_size=(x2-x1-4, y2-y1-4),
                text_style=None
            ))
            
            # Calculate text region positions relative to poster
            category_x = x2 + 10  # Start text after poster
            score_x = self.width * 0.6  # Scores start at 60% of width
            
            # Category text
            regions.append(TemplateRegion(
                x1=category_x,
                y1=y1,
                x2=score_x - 10,
                y2=y1 + (y2-y1)//2,
                content_type='text',
                identifier=f"category_{i+1}",
                original_size=(score_x - category_x - 10, (y2-y1)//2),
                text_style=text_style
            ))
            
            # Movie title
            regions.append(TemplateRegion(
                x1=category_x,
                y1=y1 + (y2-y1)//2,
                x2=score_x - 10,
                y2=y2,
                content_type='text',
                identifier=f"movie_{i+1}",
                original_size=(score_x - category_x - 10, (y2-y1)//2),
                text_style=text_style
            ))
            
            # Tomato score
            regions.append(TemplateRegion(
                x1=score_x,
                y1=y1,
                x2=score_x + (self.width - score_x)//2,
                y2=y2,
                content_type='score',
                identifier=f"tomato_score_{i+1}",
                original_size=((self.width - score_x)//2, y2-y1),
                text_style=text_style
            ))
            
            # Popcorn score
            regions.append(TemplateRegion(
                x1=score_x + (self.width - score_x)//2,
                y1=y1,
                x2=self.width - 10,
                y2=y2,
                content_type='score',
                identifier=f"popcorn_score_{i+1}",
                original_size=((self.width - score_x)//2, y2-y1),
                text_style=text_style
            ))
        
        # Add header regions based on score columns
        first_poster = poster_boxes[0]
        header_y = first_poster[0] - row_height//2
        
        regions.append(TemplateRegion(
            x1=score_x,
            y1=header_y,
            x2=score_x + (self.width - score_x)//2,
            y2=first_poster[0] - 10,
            content_type='text',
            identifier='header_critics',
            original_size=((self.width - score_x)//2, row_height//2),
            text_style=text_style
        ))
        
        regions.append(TemplateRegion(
            x1=score_x + (self.width - score_x)//2,
            y1=header_y,
            x2=self.width - 10,
            y2=first_poster[0] - 10,
            content_type='text',
            identifier='header_audience',
            original_size=((self.width - score_x)//2, row_height//2),
            text_style=text_style
        ))
        
        return regions

    def _update_visualization(self):
        """Update visualization template with current region markers"""
        self.viz_template = self.template.copy()
        
        for region in self.regions:
            # Convert coordinates to integers and create proper tuples
            pt1 = (int(region.x1), int(region.y1))
            pt2 = (int(region.x2), int(region.y2))
            
            if region.content_type == 'image':
                # Draw orange outer rectangle
                cv2.rectangle(self.viz_template,
                            pt1,
                            pt2,
                            (0, 69, 255),  # BGR format
                            2)
                
                # Draw red inner rectangle
                inner_pt1 = (pt1[0] - 1, pt1[1] - 1)
                inner_pt2 = (pt2[0] + 1, pt2[1] + 1)
                cv2.rectangle(self.viz_template,
                            inner_pt1,
                            inner_pt2,
                            (0, 0, 255),  # BGR format
                            1)
            else:
                # Draw blue rectangle for text/score regions
                cv2.rectangle(self.viz_template,
                            pt1,
                            pt2,
                            (255, 0, 0),  # BGR format
                            1)
                
                # Add region identifier text for debugging
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.4
                cv2.putText(self.viz_template,
                        region.identifier,
                        (pt1[0], pt1[1] - 5),
                        font,
                        font_scale,
                            (0, 0, 0),
                            1)

    def _get_matching_font(self, text_style: TextStyle) -> ImageFont:
        """Get a font matching the detected style"""
        font_path = self.system_fonts.get(text_style.font_family.lower(), self.system_fonts['arial'])
        try:
            font = ImageFont.truetype(font_path, text_style.font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        return font


    def replace_content(self, region_identifier: str, new_content: any) -> bool:
        """Replace content in specified region"""
        matching_regions = [r for r in self.regions if r.identifier == region_identifier]
        if not matching_regions:
            print(f"No region found with identifier: {region_identifier}")
            return False
        
        region = matching_regions[0]
        
        if region.content_type == 'image':
            if isinstance(new_content, str):
                try:
                    new_image = cv2.imread(new_content)
                    if new_image is None:
                        print(f"Could not load image from {new_content}")
                        return False
                    
                    # Resize to fit region
                    new_image = cv2.resize(new_image, 
                                         (region.x2 - region.x1, region.y2 - region.y1))
                    
                    # Clear region and place new image
                    self.template[region.y1:region.y2, region.x1:region.x2] = new_image
                    
                    # Update PIL template
                    self.pil_template = Image.fromarray(cv2.cvtColor(self.template, cv2.COLOR_BGR2RGB))
                    self.draw = ImageDraw.Draw(self.pil_template)
                    
                    return True
                except Exception as e:
                    print(f"Error replacing image: {e}")
                    return False
        else:  # text or score
            if isinstance(new_content, (str, int, float)):
                text = str(new_content)
                
                # Clear region - Fix coordinates format
                pt1 = (int(region.x1), int(region.y1))
                pt2 = (int(region.x2), int(region.y2))
                cv2.rectangle(self.template,
                            pt1,
                            pt2,
                            (255, 255, 255),
                            -1)
                
                # Update PIL template
                self.pil_template = Image.fromarray(cv2.cvtColor(self.template, cv2.COLOR_BGR2RGB))
                self.draw = ImageDraw.Draw(self.pil_template)
                
                # Calculate font size to fit region height
                region_height = region.y2 - region.y1
                font_size = int(region_height * 0.7)  # 70% of region height
                
                try:
                    font_path = self.system_fonts.get('arial', '')
                    font = ImageFont.truetype(font_path, font_size)
                    
                    # Adjust font size until text fits width
                    text_bbox = self.draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    while text_width > (region.x2 - region.x1) and font_size > 12:
                        font_size -= 2
                        font = ImageFont.truetype(font_path, font_size)
                        text_bbox = self.draw.textbbox((0, 0), text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                except:
                    print("Error loading font, using default")
                    font = ImageFont.load_default()
                    text_bbox = self.draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                
                # Center text in region
                text_height = text_bbox[3] - text_bbox[1]
                x = region.x1 + (region.x2 - region.x1 - text_width) // 2
                y = region.y1 + (region.y2 - region.y1 - text_height) // 2
                
                # Draw text
                self.draw.text((x, y), text, font=font, fill=(0, 0, 0))
                
                # Update CV2 template
                self.template = cv2.cvtColor(np.array(self.pil_template), cv2.COLOR_RGB2BGR)
                
                return True
        
            return False

    def _get_system_fonts(self) -> Dict[str, str]:
        """Get system font paths based on OS"""
        font_paths = {}
        if os.name == 'nt':  # Windows
            font_dir = Path(os.environ['WINDIR']) / 'Fonts'
            font_paths['arial'] = str(font_dir / 'arial.ttf')
        else:  # Unix-like
            font_paths['arial'] = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            if not os.path.exists(font_paths['arial']):
                # Try alternative locations
                alternatives = [
                    '/usr/share/fonts/TTF/DejaVuSans.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                    '/System/Library/Fonts/Arial.ttf'  # For macOS
                ]
                for alt in alternatives:
                    if os.path.exists(alt):
                        font_paths['arial'] = alt
                        break
        
        return font_paths

    def save_template(self, output_path: str, save_visualization: bool = True):
        """Save modified template and visualization"""
        cv2.imwrite(output_path, self.template)
        if save_visualization:
            viz_path = output_path.rsplit('.', 1)[0] + '_regions.' + output_path.rsplit('.', 1)[1]
            cv2.imwrite(viz_path, self.viz_template)

    def get_region_info(self) -> Dict[str, TemplateRegion]:
        """Return dictionary of all regions and their properties"""
        return {region.identifier: region for region in self.regions}

def main():
    template_manager = TemplateManager('template3.jpg')

    # Check detected regions
    regions = template_manager.get_region_info()
    for identifier, region in regions.items():
        print(f"Detected: {identifier}")

    # Test replacements
    template_manager.replace_content('category_1', 'Action')
    template_manager.replace_content('movie_1', 'The Dark Knight')
    template_manager.replace_content('tomato_score_1', '94%')
    template_manager.replace_content('popcorn_score_1', '96%')
    template_manager.replace_content('poster_1', 'movie_poster.jpg')

    template_manager.save_template('output.jpg')

if __name__ == "__main__":
    main()
