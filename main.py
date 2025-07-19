#!/usr/bin/env python3
"""
Bacteria Detection API

A FastAPI-based web service for detecting and counting bacteria in microscopy images
using a trained YOLOv8 model.

Author: Bacteria Detection Team
Version: 1.0.0
"""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import cv2
import tempfile
from pathlib import Path
import os
import sys

# Initialize FastAPI app
app = FastAPI(
    title="Bacteria Detection API",
    version="1.0.0",
    description="Automated bacteria detection and counting using YOLOv8",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variable
model = None

def load_model():
    """Load the YOLO model with error handling"""
    global model
    try:
        from ultralytics import YOLO
        MODEL_PATH = "bacteria_detector_final_n.pt"
        
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        
        print(f"Loading model from: {MODEL_PATH}")
        model = YOLO(MODEL_PATH)
        print("✅ Model loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

# Try to load model at startup
print("🔄 Initializing Bacteria Detection API...")
model_loaded = load_model()

@app.get("/")
def root():
    """
    Root endpoint - API status and information.
    
    Returns:
        dict: API status, model status, and available endpoints
    """
    return {
        "message": "Bacteria Detection API is running",
        "model_loaded": model is not None,
        "endpoints": {
            "detect": "/detect/ (POST) - Upload image for bacteria detection",
            "docs": "/docs - API documentation"
        }
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Service health status and model availability
    """
    return {
        "status": "healthy" if model is not None else "model_not_loaded",
        "model_loaded": model is not None
    }

@app.post("/detect/")
async def detect_bacteria(file: UploadFile = File(...)):
    """
    Detect bacteria in an uploaded image.
    
    Args:
        file: Uploaded image file (PNG, JPG, JPEG, TIFF, BMP)
    
    Returns:
        JSON response with bacteria count, detections, and metadata
    """
    tmp_path = None
    try:
        # Check if model is loaded
        if model is None:
            return JSONResponse(
                {"error": "Model not loaded. Please check server logs."}, 
                status_code=503
            )
        
        # Validate file type
        if not file.filename:
            return JSONResponse(
                {"error": "No filename provided"}, 
                status_code=400
            )
        
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return JSONResponse(
                {"error": f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"}, 
                status_code=400
            )
        
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        print(f"🔍 Processing image: {file.filename} ({len(content)} bytes)")

        # Run inference
        results = model(tmp_path, verbose=False)
        bacteria_count = 0
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                bacteria_count = len(boxes)
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    detections.append({
                        "id": i + 1,
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "confidence": float(conf),
                        "center_x": float((x1 + x2) / 2),
                        "center_y": float((y1 + y2) / 2),
                        "width": float(x2 - x1),
                        "height": float(y2 - y1)
                    })
        
        print(f"✅ Detection complete: {bacteria_count} bacteria found")
        
        return JSONResponse({
            "bacteria_count": bacteria_count,
            "detections": detections,
            "image_info": {
                "filename": file.filename,
                "size_bytes": len(content)
            }
        })
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return JSONResponse(
            {"error": f"Error processing image: {str(e)}"}, 
            status_code=500
        )
        
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception as cleanup_error:
                print(f"⚠️ Warning: Could not clean up temp file: {cleanup_error}")

if __name__ == "__main__":
    """
    Main execution block - starts the FastAPI server.
    """
    print("🚀 Starting Bacteria Detection API...")
    
    if model_loaded:
        print("✅ Model loaded successfully - API ready!")
        print("📍 Server will be available at: http://localhost:8000")
        print("📖 API Documentation: http://localhost:8000/docs")
    else:
        print("⚠️  Model failed to load - API will return errors")
        print("🔧 Check the model file and dependencies")
    
    print("-" * 50)
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
