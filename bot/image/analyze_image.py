import io
import os
from pathlib import Path

import cv2
import numpy as np

from bot.core.config import path_settings

BOUNDARIES = [{
    1: [0.328, 0.423, 0.435, 0.521],
    2: [0.126, 0.218, 0.352, 0.444],
    3: [0.473, 0.558, 0.435, 0.521],
    4: [0.267, 0.356, 0.352, 0.444],
    5: [0.061, 0.165, 0.279, 0.368],
    6: [0.399, 0.488, 0.352, 0.444],
    7: [0.201, 0.284, 0.279, 0.368],
    8: [0.538, 0.633, 0.352, 0.444],
    9: [0.328, 0.422, 0.279, 0.368],
    10: [0.126, 0.217, 0.206, 0.292],
    11: [0.472, 0.558, 0.279, 0.368],
    12: [0.267, 0.356, 0.206, 0.292],
    13: [0.399, 0.488, 0.206, 0.292],
    -1: [0.115, 0.225, 0.800, 0.920]
},
{
    1: [0.473, 0.558, 0.435, 0.521],
    2: [0.061, 0.165, 0.279, 0.368],
    3: [0.471, 0.560, 0.279, 0.369],
    4: [0.267, 0.356, 0.206, 0.292],
    5: [0.399, 0.488, 0.206, 0.292],
    6: [0.529, 0.619, 0.207, 0.296],
    7: [0.335, 0.424, 0.142, 0.231],
    8: [0.720, 0.810, 0.142, 0.231],
    9: [0.343, 0.436, 0.006, 0.099],
    -1: [0.115, 0.225, 0.800, 0.920]
}]

# RECT_FOLDER = 'Cropped_Rectangles'
CIRCLE_TEMPLATE_SIZE = (96, 96)
RECT_TEMPLATE_SIZE = (110, 118)

class Analyze_Image:
    """Analyze formation images to extract unit and artifact positions."""
    def __init__(self):
        """Initialize analyzer and load template images."""
        self.clear()
        
        self.circ_templates = {}
        for file_path in path_settings.templates_folder.iterdir():
            if file_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
                input_img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
                if input_img is None:
                    raise ValueError
                
                name = file_path.stem
                template = cv2.resize(input_img, CIRCLE_TEMPLATE_SIZE, interpolation=cv2.INTER_AREA)
                self.circ_templates[name] = template
        """
        self.rect_templates = {}
        for filename in os.listdir(RECT_FOLDER):
            # For all images
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                file_path = os.path.join(RECT_FOLDER, filename)
                # Read image
                input_img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
                if input_img is None:
                    raise ValueError
                
                # Get filename w/o extension
                name = os.path.splitext(os.path.basename(filename))[0]
                # Store in dict
                template = self.pad_to_aspect(input_img, RECT_TEMPLATE_SIZE[0] / RECT_TEMPLATE_SIZE[1])
                template = cv2.resize(template, RECT_TEMPLATE_SIZE, interpolation=cv2.INTER_AREA)
                self.rect_templates[name] = template
        """
                
    def clear(self):
        """Reset all analysis state."""
        self.image = None
        self.gray = None
        self.height = 0
        self.width = 0
        self.diameter = 0
        self.minRadius = 0
        self.circles_pos = []
        self.circles = []
        self.units = []
        self.artifact = None
        self.rectangle = None
        
    def process_image(self, image_bytes, rr_map: bool=False):
        """Process image bytes to extract formation data."""
        self.clear()
        
        np_array = np.frombuffer(image_bytes, np.uint8)
        self.image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Crop the image to the white border
        self.image = self.crop_image()
        if self.image is None:
            return None, None, None
        
        # If image was too small, this is not valid
        self.height, self.width = self.image.shape[:2]
        if self.height < 30 or self.width < 30:
            return None, None, None
        
        map_type = 1 if rr_map else 0
        # Calculate bounds based on current image dimensions
        self.bounds = {key : [value[0] * self.width,
                              value[1] * self.width,
                              value[2] * self.height,
                              value[3] * self.height]
                        for key, value in BOUNDARIES[map_type].items()}
        
        self.get_rectangle()
        # Remove bottom section, stripping off the investment section
        self.height = int(self.height * 2 / 3)
        self.image = self.image[:self.height, :self.width]
        self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Calculate approximate size of circles
        self.diameter = self.bounds[1][1] - self.bounds[1][0]
        self.minRadius = int(self.diameter / 3)
        
        # Get position of circles via Hough
        self.get_circles_pos()
        
        # Crop the circles
        self.get_circles()
        
        # Get tile numbers and character names
        return self.categorize()

    def pad_to_aspect(self, image, aspect_ratio):
        """Pad image to match target aspect ratio."""
        h, w = image.shape[:2]
        current_ratio = w / h

        if current_ratio > aspect_ratio:
            new_h = int(w / aspect_ratio)
            pad = (new_h - h) // 2
            padded = cv2.copyMakeBorder(image, pad, pad, 0, 0, cv2.BORDER_CONSTANT, value=0)
        else:
            new_w = int(h * aspect_ratio)
            pad = (new_w - w) // 2
            padded = cv2.copyMakeBorder(image, 0, 0, pad, pad, cv2.BORDER_CONSTANT, value=0)

        return padded
    
    def get_rectangle(self):
        """Extract rectangle region for artifact detection."""
        int_bounds = [int(bound) for bound in self.bounds[-1]]
        self.rectangle = self.image[int_bounds[2]:int_bounds[3], int_bounds[0]:int_bounds[1]]
        
    def add_unit(self, unit_name, tile_number, image):
        """Create unit dictionary with name, tile number, and image bytes."""
        success, encoded_image = cv2.imencode('.png', image)
        byte_stream = None
        if success:
            byte_stream = io.BytesIO(encoded_image.tobytes())
            byte_stream.seek(0)
        
        return {
            'name': unit_name,
            'number': tile_number,
            'image': byte_stream}
        
    def categorize(self) -> list[dict]:
        """Categorize all detected circles and return unit list."""
        """
        success, encoded_image = cv2.imencode('.png', self.image)
        image_byte_stream = None
        if success:
            image_byte_stream = io.BytesIO(encoded_image.tobytes())
            image_byte_stream.seek(0)
        """
            
        # unit_name = self.categorize_rectangle()
        #self.artifact = self.add_unit(unit_name, -1, self.rectangle)
            
        for i in range(len(self.circles_pos) - 1, -1, -1):
            tile_number, unit_name = self.categorize_circle(i)
            if unit_name == "None" or tile_number == 0:
                continue
            self.units.append(self.add_unit(unit_name, tile_number, self.circles[i]))
            
        #return image_byte_stream,
        return self.units
        #, self.artifact
        
    def save_circles(self):
        """Save detected circles to temp directory for debugging."""
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        filename = temp_dir / "rectangle.png"
        cv2.imwrite(str(filename), self.image)
        
        for dictionary in self.units:
            name = dictionary['name']
            number = dictionary['number']
            image = dictionary['image']
            filename = temp_dir / f"{name}_{number}.png"
            cv2.imwrite(str(filename), image)
    
    def crop_image(self):
        """Crop image to remove white border."""
        _, mask = cv2.threshold(self.gray, 240, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        # assume the largest contour is border
        if contours:
            x, y, w, h = cv2.boundingRect(contours[0])
            return self.image[y+h-w:y+h, x:x+w]
        return None
    
    def get_circles_pos(self):
        """Detect circle positions using Hough circle detection."""
        gray_blurred = cv2.blur(self.gray, (3, 3))

        circles = cv2.HoughCircles(
            gray_blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=self.minRadius, 
            param1=220, param2=22, minRadius=self.minRadius, maxRadius=self.minRadius * 2
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            count = 0
            
            for pt in circles[0, :]:
                if count >= 10: # limit to 10 units
                    break
                a, b, r = pt[0], pt[1], pt[2]
                self.circles_pos.append([a, b, r])
                count += 1
                
    def get_mask(self, size):
        """Create circular mask for template matching."""
        h, w = size
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        radius = min(center)
        cv2.circle(mask, center, radius, 255, -1)
        return mask
                
    def get_circles(self):
        """Extract circular regions from detected positions."""
        for a, b, r in self.circles_pos:
            x1, y1 = max(a - r, 0), max(b - r, 0)
            x2, y2 = min(a + r, self.width), min(b + r, self.height)
            
            mask = np.zeros((2*r, 2*r, 3), dtype=np.uint8)
            cv2.circle(mask, (r, r), r, (255, 255, 255), -1)

            cropped_rectangle = self.image[y1:y2, x1:x2]
            result = np.zeros_like(mask)
            result[:cropped_rectangle.shape[0], :cropped_rectangle.shape[1]] = cropped_rectangle
            cropped_circle = cv2.bitwise_and(result, mask)
            height, width = cropped_circle.shape[:2]
            size = min(height, width)
            cropped_circle = cropped_circle[:size, :size]
            self.circles.append(cropped_circle)
            
    """
    def categorize_rectangle(self):
        rectangle = self.rectangle
        if rectangle.shape[2] == 4:
            rectangle = cv2.cvtColor(rectangle, cv2.COLOR_BGRA2BGR)

        aspect = RECT_TEMPLATE_SIZE[0] / RECT_TEMPLATE_SIZE[1]
        input_padded = self.pad_to_aspect(rectangle, aspect)
        input_resized = cv2.resize(input_padded, RECT_TEMPLATE_SIZE, interpolation=cv2.INTER_AREA)

        best_score = -1
        best_label = None

        for label, template in self.rect_templates.items():
            result = cv2.matchTemplate(input_resized, template, cv2.TM_CCOEFF_NORMED)
            _, score, _, _ = cv2.minMaxLoc(result)
            #print(score)
            #print(label)
            if score > best_score:
                best_score = score
                best_label = label.split('_', 1)[0]

        return best_label
    """
    
    def categorize_circle(self, index):
        """Identify tile position and unit name for a detected circle."""
        a, b, r = self.circles_pos[index]
        x1, y1 = max(a - r, 0), max(b - r, 0)
        x2, y2 = min(a + r, self.width), min(b + r, self.height)
    
        tile = 0
        for key, values in self.bounds.items():
            w = (values[1] - values[0]) / 4
            h = (values[3] - values[2]) / 4
            if x1 + r > values[0] + w and x2 - r < values[1] - w and y1 + r > values[2] + h and y2 - r < values[3] - h:
                tile = key
                break
            
        circle = self.circles[index]
        if circle.shape[2] == 4:
            circle = cv2.cvtColor(circle, cv2.COLOR_BGRA2BGR)

        input_resized = cv2.resize(circle, CIRCLE_TEMPLATE_SIZE, interpolation=cv2.INTER_AREA)
        mask = self.get_mask(CIRCLE_TEMPLATE_SIZE[::-1])

        best_score = -1
        best_label = None

        for label, template in self.circ_templates.items():
            result = cv2.matchTemplate(input_resized, template, cv2.TM_CCOEFF_NORMED, mask=mask)
            _, score, _, _ = cv2.minMaxLoc(result)

            if score > best_score:
                best_score = score
                best_label = label.split('_', 1)[0]

        return tile, best_label