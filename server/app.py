from support_env.server.app import app

def main():
    import uvicorn
    import os
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("support_env.server.app:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()
