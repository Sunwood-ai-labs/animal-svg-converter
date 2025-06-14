import gradio as gr
import vtracer
import os
import shutil
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from pathlib import Path

# Helper to estimate area of a path by bounding box
def _path_area(path_data):
    coords = re.findall(r"(-?\d+\.?\d*)[, ]+(-?\d+\.?\d*)", path_data)
    if not coords:
        return 0
    xs = [float(x) for x, _ in coords]
    ys = [float(y) for _, y in coords]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


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


def convert_image(image_path, output_dir, remove_bg=False):
    base = os.path.splitext(os.path.basename(image_path))[0]
    svg_path = os.path.join(output_dir, f"{base}.svg")
    vtracer.convert_image_to_svg_py(image_path, svg_path)
    if remove_bg:
        remove_largest_path(svg_path)
    return svg_path


def make_preview_html(original, converted):
    """Return HTML snippet showing original and converted images using Gradio's file serving."""
    return (
        f'<div style="display:flex;gap:10px;margin-bottom:1em;border:1px solid #ddd;padding:10px;border-radius:5px">'
        f'<div style="text-align:center"><p><strong>Original</strong></p>'
        f'<img src="/gradio_api/file={original}" style="max-width:200px;max-height:200px;border:1px solid #ccc"></div>'
        f'<div style="text-align:center"><p><strong>Converted SVG</strong></p>'
        f'<img src="/gradio_api/file={converted}" style="max-width:200px;max-height:200px;border:1px solid #ccc"></div>'
        f'</div>'
    )


def convert_images_to_svgs(files, remove_bg=False):
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
            
        # SVGに変換
        svg_path = convert_image(str(orig_copy), str(output_dir), remove_bg=remove_bg)
        svg_paths.append(svg_path)
        
        # プレビュー作成 - 相対パスを使用
        rel_orig = os.path.relpath(orig_copy, Path.cwd())
        rel_svg = os.path.relpath(svg_path, Path.cwd())
        preview_html = make_preview_html(rel_orig, rel_svg)
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
                btn = gr.Button("Convert to SVG", variant="primary")
            
        with gr.Row():
            out_files = gr.Files(label="Download Converted SVG Files")
            
        with gr.Row():
            preview = gr.HTML(label="Preview")
        
        btn.click(
            fn=convert_images_to_svgs, 
            inputs=[inp, remove_bg], 
            outputs=[out_files, preview]
        )
        
    return demo


def main():
    demo = build_app()
    demo.launch(show_error=True)


if __name__ == "__main__":
    main()
