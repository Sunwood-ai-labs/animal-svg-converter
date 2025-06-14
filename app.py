import gradio as gr
import vtracer
import os
import tempfile
import xml.etree.ElementTree as ET
import re

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

# Convert a single image to SVG and return path

def convert_image(image_path, output_dir, remove_bg=False):
    base = os.path.splitext(os.path.basename(image_path))[0]
    svg_path = os.path.join(output_dir, f"{base}.svg")
    vtracer.convert_image_to_svg_py(image_path, svg_path)
    if remove_bg:
        remove_largest_path(svg_path)
    return svg_path


def make_preview_html(original, converted):
    """Return HTML snippet showing original and converted images."""
    return (
        f'<div style="display:flex;gap:10px;margin-bottom:1em">'
        f'<div><p>Original</p><img src="file={original}" style="max-width:200px"></div>'
        f'<div><p>Converted</p><img src="file={converted}" style="max-width:200px"></div>'
        f'</div>'
    )


def convert_images_to_svgs(files, remove_bg=False):
    """Convert uploaded images to SVG and return file paths and preview HTML."""
    if not files:
        return [], ""

    output_dir = tempfile.mkdtemp()
    svg_paths = []
    previews = []
    for file_obj in files:
        if hasattr(file_obj, 'name'):
            path = file_obj.name
        else:
            path = file_obj
        svg_path = convert_image(path, output_dir, remove_bg=remove_bg)
        svg_paths.append(svg_path)
        previews.append(make_preview_html(path, svg_path))

    preview_html = "\n".join(previews)
    return svg_paths, preview_html


def build_app():
    with gr.Blocks() as demo:
        gr.Markdown("## Image to SVG Converter")
        gr.Markdown("Upload multiple images and download converted SVG files.")
        with gr.Row():
            inp = gr.File(file_count="multiple", label="Input Images")
            remove_bg = gr.Checkbox(label="Remove largest element", value=False)
        out_files = gr.Files(label="Converted SVGs")
        preview = gr.HTML()
        btn = gr.Button("Convert")
        btn.click(fn=convert_images_to_svgs, inputs=[inp, remove_bg], outputs=[out_files, preview])
    return demo


def main():
    demo = build_app()
    demo.launch()


if __name__ == "__main__":
    main()
