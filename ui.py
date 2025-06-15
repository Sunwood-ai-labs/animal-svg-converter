import gradio as gr
from pathlib import Path
from converter import convert_images_to_svgs

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
                llm_filename = gr.Checkbox(
                    label="Suggest unique English file names with LLM",
                    value=False
                )
                asset_prefix = gr.Textbox(
                    label="Asset prefix for file names",
                    value=""
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
                llm_filename,
                asset_prefix,
            ],
            outputs=[out_files, preview]
        )
        
    return demo