import asyncio
import sys
import uvicorn

if __name__ == "__main__":
    if len(sys.argv) > 1 and any(arg in sys.argv for arg in ["--cli", "--demo", "--adversarial", "-a"]):
        from app.cli import main
        asyncio.run(main())
    else:
        print("Starting VERITAS Proof-Carrying Data Analyst API on http://127.0.0.1:8000 ...")
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

