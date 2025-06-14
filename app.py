import gradio as gr
import vtracer
import os
import tempfile

# Convert a single image to SVG and return path

def convert_image(image_path, output_dir):
    base = os.path.splitext(os.path.basename(image_path))[0]
    svg_path = os.path.join(output_dir, f"{base}.svg")
    vtracer.convert_image_to_svg_py(image_path, svg_path)
    return svg_path


def convert_images_to_svgs(files):
    """Convert uploaded images to SVG and return list of SVG file paths."""
    if not files:
        return []

    output_dir = tempfile.mkdtemp()
    svg_paths = []
    for file_obj in files:
        if hasattr(file_obj, 'name'):
            path = file_obj.name
        else:
            path = file_obj
        svg_path = convert_image(path, output_dir)
        svg_paths.append(svg_path)

    return svg_paths


def build_app():
    with gr.Blocks() as demo:
        gr.Markdown("## Image to SVG Converter")
        gr.Markdown("Upload multiple images and download converted SVG files.")
        with gr.Row():
            inp = gr.File(file_count="multiple", label="Input Images")
        out_files = gr.Files(label="Converted SVGs")
        btn = gr.Button("Convert")
        btn.click(fn=convert_images_to_svgs, inputs=inp, outputs=out_files)
    return demo


def main():
    demo = build_app()
    demo.launch()


if __name__ == "__main__":
    main()
