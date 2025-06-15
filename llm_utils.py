import base64
from litellm import completion

def suggest_filename_with_llm(image_path):
    """
    画像ファイルからLLM（Gemini）で英語のユニークなファイル名を提案する
    """
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        prompt_text = (
            "You are an assistant that generates unique, short, descriptive English file names for icon images. "
            "Given the following icon image, suggest a unique English file name (no extension, no spaces, use only a-z, 0-9, hyphens or underscores):"
        )
        response = completion(
            model="gemini/gemini-2.5-flash-preview-05-20",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }
            ]
        )
        # レスポンスからファイル名部分のみ抽出（属性アクセスに修正）
        name = response.choices[0].message.content.strip()
        # 拡張子やスペースを除去
        name = name.split(".")[0].replace(" ", "_")
        # 許可文字以外を除去（a-z, 0-9, -, _ のみ許可）
        import re
        name = re.sub(r'[^a-z0-9\-_]', '', name.lower())
        return name
    except Exception as e:
        print(f"LLM filename suggestion failed: {e}")
        return None