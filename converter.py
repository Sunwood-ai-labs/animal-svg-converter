import base64
from llm_utils import suggest_filename_with_llm
import os
import os
import shutil
from datetime import datetime
from pathlib import Path
import vtracer

from utils import crop_image_whitespace, remove_largest_path

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
    svg_filename=None,
):
    if svg_filename:
        svg_path = os.path.join(output_dir, svg_filename)
    else:
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
    use_llm_filename=False,
    asset_prefix="",
):
    """Convert uploaded images to SVG and return file paths and preview HTML."""
    if not files:
        return [], "<p>No files uploaded.</p>"

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
            
        ext = os.path.splitext(path)[1]
        orig_copy = output_dir / f"input_{i+1}{ext}"
        
        try:
            shutil.copy(path, orig_copy)
        except Exception as e:
            print(f"Failed to copy {path}: {e}")
            continue
        
        if crop_whitespace:
            cropped_name = f"cropped_{i+1}{ext}"
            cropped_path = output_dir / cropped_name
            crop_image_whitespace(str(orig_copy), str(cropped_path))
            input_for_svg = str(cropped_path)
            preview_image = cropped_path
        else:
            input_for_svg = str(orig_copy)
            preview_image = orig_copy

        # ファイル名生成
        if use_llm_filename:
            llm_name = suggest_filename_with_llm(input_for_svg)
            if llm_name:
                base_name = llm_name
            else:
                base_name = f"image_{i+1}"
        else:
            base_name = f"image_{i+1}"
        if asset_prefix:
            base_name = f"{asset_prefix}{base_name}"
        svg_filename = f"{base_name}.svg"

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
            svg_filename=svg_filename,
        )
        svg_paths.append(svg_path)
        
        rel_preview = os.path.relpath(preview_image, Path.cwd())
        rel_svg = os.path.relpath(svg_path, Path.cwd())
        preview_html = make_preview_html(rel_preview, rel_svg)
        previews.append(preview_html)

    if not previews:
        return [], "<p>No files were successfully processed.</p>"
    
    combined_preview = "<div>" + "\n".join(previews) + "</div>"
    return svg_paths, combined_preview