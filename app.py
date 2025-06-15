from dotenv import load_dotenv
load_dotenv()
from ui import build_app

def main():
    demo = build_app()
    demo.launch(show_error=True)

if __name__ == "__main__":
    main()
