import cv2
import numpy as np
from typing import Tuple, Optional

class OpenCVFontHandler:
    def __init__(self):
        self.base_font = cv2.FONT_HERSHEY_DUPLEX
        self.base_font_size = 16
        
    def get_font_scale(self, desired_size: int) -> float:
        """Convert desired font size to OpenCV font scale"""
        return desired_size / self.base_font_size
    
    def get_text_size(self, text: str, font_size: int) -> Tuple[int, int]:
        """Get the pixel dimensions of text at specified font size"""
        font_scale = self.get_font_scale(font_size)
        (width, height), baseline = cv2.getTextSize(
            text, 
            self.base_font, 
            font_scale, 
            thickness=1
        )
        return width, height + baseline
    
    def put_text(self, 
                img: np.ndarray, 
                text: str, 
                position: Tuple[int, int], 
                font_size: int, 
                color: Tuple[int, int, int],
                thickness: int = 1,
                outline_color: Optional[Tuple[int, int, int]] = None,
                outline_thickness: int = 2) -> None:
        """Draw text with optional outline"""
        font_scale = self.get_font_scale(font_size)
        
        # Draw outline if specified
        if outline_color is not None:
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                cv2.putText(
                    img,
                    text,
                    (position[0] + dx, position[1] + dy),
                    self.base_font,
                    font_scale,
                    outline_color,
                    outline_thickness,
                    cv2.LINE_AA
                )
        
        # Draw main text
        cv2.putText(
            img,
            text,
            position,
            self.base_font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA
        )
    
    def put_multiline_text(self,
                          img: np.ndarray,
                          text: str,
                          position: Tuple[int, int],
                          font_size: int,
                          color: Tuple[int, int, int],
                          line_spacing: int = 10,
                          **text_kwargs) -> int:
        """Draw multi-line text and return total height"""
        x, y = position
        height = 0
        
        for line in text.split('\n'):
            self.put_text(img, line, (x, y + height), font_size, color, **text_kwargs)
            _, line_height = self.get_text_size(line, font_size)
            height += line_height + line_spacing
        
        return height
