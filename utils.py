import os
import shutil
import re
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

def _path_area(path_data):
    coords = re.findall(r"(-?\d+\.?\d*)[, ]+(-?\d+\.?\d*)", path_data)
    if not coords:
        return 0
    xs = [float(x) for x, _ in coords]
    ys = [float(y) for _, y in coords]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))

def crop_image_whitespace(image_path, output_path):
    """Remove whitespace/margins from image by cropping to content bounds."""
    try:
        with Image.open(image_path) as img:
            img_array = np.array(img)
            
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            threshold = np.mean(gray) * 0.95
            mask = gray < threshold
            
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            
            if np.any(rows) and np.any(cols):
                rmin, rmax = np.where(rows)[0][[0, -1]]
                cmin, cmax = np.where(cols)[0][[0, -1]]
                
                cropped = img.crop((cmin, rmin, cmax + 1, rmax + 1))
                cropped.save(output_path)
                return output_path
            else:
                img.save(output_path)
                return output_path
    except Exception as e:
        print(f"Error cropping image {image_path}: {e}")
        shutil.copy(image_path, output_path)
        return output_path

def remove_largest_path(svg_file):
    """Remove the path with the largest bounding box area from an SVG."""
    try:
        tree = ET.parse(svg_file)
    except Exception:
        return

    root = tree.getroot()
    paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    if not paths:
        paths = root.findall('.//path')

    largest = None
    largest_area = 0
    for p in paths:
        area = _path_area(p.get('d', ''))
        if area > largest_area:
            largest_area = area
            largest = p

    if largest is None:
        return

    parent = None
    for elem in root.iter():
        for child in list(elem):
            if child is largest:
                parent = elem
                break

    if parent is not None:
        parent.remove(largest)
        tree.write(svg_file)