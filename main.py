#!/usr/bin/env python3
"""
Main entry point for the FastAPI application.
This file only contains the Uvicorn server configuration.
The actual FastAPI app is defined in app.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )
