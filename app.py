import gradio as gr
import vtracer
import os
import shutil
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from pathlib import Path
from PIL import Image
import numpy as np

# Helper to estimate area of a path by bounding box
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


def convert_image(
    image_path,
    output_dir,
    remove_bg=False,
    *,
    colormode="color",
    hierarchical="stacked",
    mode="spline",
    filter_speckle=4,
    color_precision=6,
    layer_difference=16,
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=8,
):
    base = os.path.splitext(os.path.basename(image_path))[0]
    svg_path = os.path.join(output_dir, f"{base}.svg")
    vtracer.convert_image_to_svg_py(
        image_path,
        svg_path,
        colormode=colormode,
        hierarchical=hierarchical,
        mode=mode,
        filter_speckle=filter_speckle,
        color_precision=color_precision,
        layer_difference=layer_difference,
        corner_threshold=corner_threshold,
        length_threshold=length_threshold,
        max_iterations=max_iterations,
        splice_threshold=splice_threshold,
        path_precision=path_precision,
    )
    if remove_bg:
        remove_largest_path(svg_path)
    return svg_path


def make_preview_html(input_image, converted):
    """Return HTML snippet showing input and converted images using Gradio's file serving."""
    return (
        f'<div style="display:flex;gap:10px;margin-bottom:1em;border:1px solid #ddd;padding:10px;border-radius:5px">'
        f'<div style="text-align:center"><p><strong>Input</strong></p>'
        f'<img src="/gradio_api/file={input_image}" style="max-width:200px;max-height:200px;border:1px solid #ccc"></div>'
        f'<div style="text-align:center"><p><strong>Converted SVG</strong></p>'
        f'<img src="/gradio_api/file={converted}" style="max-width:200px;max-height:200px;border:1px solid #ccc"></div>'
        f'</div>'
    )


def convert_images_to_svgs(
    files,
    remove_bg=False,
    crop_whitespace=True,
    colormode="color",
    hierarchical="stacked",
    mode="spline",
    filter_speckle=4,
    color_precision=6,
    layer_difference=16,
    corner_threshold=60,
    length_threshold=4.0,
    max_iterations=10,
    splice_threshold=45,
    path_precision=8,
):
    """Convert uploaded images to SVG and return file paths and preview HTML."""
    if not files:
        return [], "<p>No files uploaded.</p>"

    # 作業ディレクトリ内にassetディレクトリを作成
    assets_dir = Path.cwd() / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = assets_dir / f"svg_conversion_{timestamp}"
    output_dir.mkdir(exist_ok=True)
    
    svg_paths = []
    previews = []
    
    for i, file_obj in enumerate(files):
        if hasattr(file_obj, 'name'):
            path = file_obj.name
        else:
            path = file_obj
            
        # ファイル名を簡素化
        ext = os.path.splitext(path)[1]
        simple_name = f"input_{i+1}{ext}"
        orig_copy = output_dir / simple_name
        
        try:
            shutil.copy(path, orig_copy)
        except Exception as e:
            print(f"Failed to copy {path}: {e}")
            continue
        
        # 余白を削除してクロップ（オプション）
        if crop_whitespace:
            cropped_name = f"cropped_{i+1}{ext}"
            cropped_path = output_dir / cropped_name
            crop_image_whitespace(str(orig_copy), str(cropped_path))
            input_for_svg = str(cropped_path)
            preview_image = cropped_path
        else:
            input_for_svg = str(orig_copy)
            preview_image = orig_copy
            
        # SVGに変換
        svg_path = convert_image(
            input_for_svg,
            str(output_dir),
            remove_bg=remove_bg,
            colormode=colormode,
            hierarchical=hierarchical,
            mode=mode,
            filter_speckle=filter_speckle,
            color_precision=color_precision,
            layer_difference=layer_difference,
            corner_threshold=corner_threshold,
            length_threshold=length_threshold,
            max_iterations=max_iterations,
            splice_threshold=splice_threshold,
            path_precision=path_precision,
        )
        svg_paths.append(svg_path)
        
        # プレビュー作成 - 相対パスを使用
        rel_preview = os.path.relpath(preview_image, Path.cwd())
        rel_svg = os.path.relpath(svg_path, Path.cwd())
        preview_html = make_preview_html(rel_preview, rel_svg)
        previews.append(preview_html)

    if not previews:
        return [], "<p>No files were successfully processed.</p>"
    
    combined_preview = "<div>" + "\n".join(previews) + "</div>"
    return svg_paths, combined_preview


def build_app():
    # assetsディレクトリを静的パスとして設定
    assets_path = Path.cwd() / "assets"
    assets_path.mkdir(exist_ok=True)
    gr.set_static_paths(paths=[assets_path])
    
    with gr.Blocks(title="Image to SVG Converter") as demo:
        gr.Markdown("# Image to SVG Converter")
        gr.Markdown("Upload multiple images and convert them to SVG format. Optionally remove the largest element (usually background).")
        
        with gr.Row():
            with gr.Column():
                inp = gr.File(
                    file_count="multiple", 
                    label="Upload Images",
                    file_types=["image"]
                )
                remove_bg = gr.Checkbox(
                    label="Remove largest element (background removal)",
                    value=False
                )
                crop_whitespace = gr.Checkbox(
                    label="Crop whitespace/margins",
                    value=True
                )
                colormode = gr.Radio(
                    ["color", "binary"],
                    value="color",
                    label="Color mode",
                )
                hierarchical = gr.Radio(
                    ["stacked", "cutout"],
                    value="stacked",
                    label="Hierarchy mode",
                )
                mode_option = gr.Radio(
                    ["spline", "polygon", "none"],
                    value="spline",
                    label="Trace mode",
                )
                filter_speckle = gr.Slider(
                    minimum=0,
                    maximum=20,
                    value=4,
                    step=1,
                    label="Filter speckle",
                )
                color_precision = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=6,
                    step=1,
                    label="Color precision",
                )
                layer_difference = gr.Slider(
                    minimum=1,
                    maximum=32,
                    value=16,
                    step=1,
                    label="Layer difference",
                )
                corner_threshold = gr.Slider(
                    minimum=0,
                    maximum=180,
                    value=60,
                    step=1,
                    label="Corner threshold",
                )
                length_threshold = gr.Slider(
                    minimum=3.5,
                    maximum=10.0,
                    value=4.0,
                    step=0.1,
                    label="Length threshold",
                )
                max_iterations = gr.Slider(
                    minimum=1,
                    maximum=50,
                    value=10,
                    step=1,
                    label="Max iterations",
                )
                splice_threshold = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=45,
                    step=1,
                    label="Splice threshold",
                )
                path_precision = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=8,
                    step=1,
                    label="Path precision",
                )
                btn = gr.Button("Convert to SVG", variant="primary")
            
        with gr.Row():
            out_files = gr.Files(label="Download Converted SVG Files")
            
        with gr.Row():
            preview = gr.HTML(label="Preview")
        
        btn.click(
            fn=convert_images_to_svgs,
            inputs=[
                inp,
                remove_bg,
                crop_whitespace,
                colormode,
                hierarchical,
                mode_option,
                filter_speckle,
                color_precision,
                layer_difference,
                corner_threshold,
                length_threshold,
                max_iterations,
                splice_threshold,
                path_precision,
            ],
            outputs=[out_files, preview]
        )
        
    return demo


def main():
    demo = build_app()
    demo.launch(show_error=True)


if __name__ == "__main__":
    main()
