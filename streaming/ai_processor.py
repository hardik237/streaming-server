"""
AI Processor using YOLOv8 for object detection
Processes frames from GStreamer pipeline and writes overlays
"""
import cv2
import numpy as np
from ultralytics import YOLO
import logging
import os
from datetime import datetime
from utils.db import get_db
import subprocess
import threading

logger = logging.getLogger(__name__)

class AIProcessor:
    """YOLOv8 object detection processor"""
    
    def __init__(self, stream_id, model_name="yolov8n.pt", sample_rate=2, min_confidence=0.5, 
                 rtmp_output=None, width=None, height=None, fps=10):
        self.stream_id = stream_id
        self.sample_rate = sample_rate  # Process every Nth frame
        self.min_confidence = min_confidence
        self.frame_count = 0
        self.rtmp_output = rtmp_output
        self.ffmpeg_process = None
        self.width = width
        self.height = height
        self.fps = fps
        
        # # Initialize YOLO model
        # model_path = f"/app/models/{model_name}"
        # if not os.path.exists(model_path):
        #     logger.info(f"Downloading YOLO model: {model_name}")
        #     os.makedirs("/app/models", exist_ok=True)
        
        self.model = YOLO(model_name)
        logger.info(f"YOLO model loaded for stream {stream_id}")
        
        # Start ffmpeg process if RTMP output is specified
        if self.rtmp_output and self.width and self.height:
            self._start_ffmpeg()
    
    def _start_ffmpeg(self):
        """Start ffmpeg process to push frames to RTMP"""
        try:
            command = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',  # OpenCV uses BGR
                '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps),
                '-i', '-',  # Input from stdin
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-b:v', '2000k',
                '-f', 'flv',
                self.rtmp_output
            ]
            
            self.ffmpeg_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            logger.info(f"FFmpeg process started for {self.stream_id} -> {self.rtmp_output}")
            
            # Start thread to read stderr
            def read_stderr():
                for line in self.ffmpeg_process.stderr:
                    logger.debug(f"FFmpeg [{self.stream_id}]: {line.decode().strip()}")
            
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting ffmpeg: {e}")
            self.ffmpeg_process = None
    
    def push_frame(self, frame):
        """Push a frame to ffmpeg for RTMP streaming"""
        if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            try:
                self.ffmpeg_process.stdin.write(frame.tobytes())
            except Exception as e:
                logger.error(f"Error pushing frame to ffmpeg: {e}")
                self.ffmpeg_process = None
        
    def process_frame(self, frame):
        """ 
        Process a video frame with YOLO detection
        Returns: frame with bounding boxes drawn
        """
        self.frame_count += 1
        
        # Sample frames (process every Nth frame) process at half the fps
        if self.frame_count % self.sample_rate != 0:
            # Still push original frame if RTMP output is enabled
            if self.rtmp_output:
                self.push_frame(frame)
            return frame
        
        try:
            # Run inference
            results = self.model(frame, conf=self.min_confidence, verbose=False, device='cpu')
            
            # Draw bounding boxes
            annotated_frame = frame.copy()
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    # Draw bounding box
                    color = (0, 255, 0)  # Green
                    cv2.rectangle(
                        annotated_frame,
                        (int(x1), int(y1)),
                        (int(x2), int(y2)),
                        color,
                        2
                    )
                    
                    # Draw label
                    label = f"{class_name} {confidence:.2f}"
                    cv2.putText(
                        annotated_frame,
                        label,
                        (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )
                    
                    # Collect detection data
                    detections.append({
                        "class": class_name,
                        "class_id": class_id,
                        "confidence": float(confidence),
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2)
                        }
                    })
            
            # Push frame to RTMP if enabled
            if self.rtmp_output:
                self.push_frame(annotated_frame)
            
            # # Save detections to database (if any)
            # if detections:
            #     self._save_detections(detections)
            
            return annotated_frame
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return frame
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait(timeout=5)
                logger.info(f"FFmpeg process closed for {self.stream_id}")
            except Exception as e:
                logger.error(f"Error closing ffmpeg process: {e}")
                if self.ffmpeg_process.poll() is None:
                    self.ffmpeg_process.kill()
   