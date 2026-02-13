"""
Vercel Serverless Function Entry Point
======================================
Este archivo es el punto de entrada para Vercel serverless functions.
Importa la aplicación FastAPI desde main.py y la expone como handler.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from main.py
from main import app

# Vercel expects the handler to be named 'app' or 'handler'
# FastAPI apps work directly with Vercel's Python runtime
handler = app
