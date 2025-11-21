# tests/conftest.py
import os
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app import app
from pathlib import Path

@pytest.fixture(scope="module")
def test_app():
    # Create temporary directories for testing
    test_upload_dir = Path("test_uploads")
    test_output_dir = Path("test_output")
    
    # Set up test environment
    os.environ["UPLOAD_DIR"] = str(test_upload_dir)
    os.environ["OUTPUT_DIR"] = str(test_output_dir)
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup after tests
    for dir_path in [test_upload_dir, test_output_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)

@pytest.fixture
def sample_video():
    # Create a small test video file (1 second of black video)
    test_video = Path("test_video.mp4")
    if not test_video.exists():
        import numpy as np
        import cv2
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(test_video), fourcc, 20.0, (640, 480))
        for _ in range(20):  # 1 second of video at 20fps
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            out.write(frame)
        out.release()
    return test_video