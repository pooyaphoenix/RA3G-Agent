import os
import argparse
import subprocess
import threading
import uvicorn
import time

def run_fastapi(api_port: int):
    """Run FastAPI using uvicorn."""
    print(f"🚀 Starting FastAPI backend on port {api_port} ...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=api_port, reload=False)


def run_streamlit(api_port: int, ui_port: int):
    """Run Streamlit app."""
    print(f"🎨 Starting Streamlit UI on port {ui_port} (connecting to API {api_port}) ...")
    env = os.environ.copy()
    env["FASTAPI_PORT"] = str(api_port)
    import sys
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app/ui/app_streamlit.py",
        "--server.port", str(ui_port),
        "--server.headless", "true"
    ], env=env)


def print_summary(api_port: int, ui_port: int):
    """Print a startup summary box."""
    print("\n" + "=" * 60)
    print("🧠 RA3G SYSTEM IS RUNNING")
    print("=" * 60)
    print(f"📡 FastAPI backend:   http://localhost:{api_port}")
    print(f"📡 FastAPI Swagger:   http://localhost:{api_port}/docs")
    print(f"💻 Streamlit frontend: http://localhost:{ui_port}")
    print("-" * 60)
    print("Press CTRL+C to stop both servers.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RA3G System (FastAPI + Streamlit)")
    parser.add_argument("--api-port", type=int, default=8010)
    parser.add_argument("--ui-port", type=int, default=8501)
    args = parser.parse_args()

    # Print startup summary
    print_summary(args.api_port, args.ui_port)

    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi, args=(args.api_port,), daemon=True)
    fastapi_thread.start()

    # Give FastAPI a brief head start
    time.sleep(1.5)

    # Start Streamlit (blocking)
    run_streamlit(args.api_port, args.ui_port)
