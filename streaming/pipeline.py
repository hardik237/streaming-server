"""
GStreamer pipeline controller 
"""
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import logging
import threading
import numpy as np
from ai_processor import AIProcessor
import cv2

logger = logging.getLogger(__name__)

# Initialize GStreamer
Gst.init(None)

class PipelineController:
    """Manages GStreamer pipelines for streams"""
    
    def __init__(self):
        self.pipelines = {}
        self.ai_processors = {}
        self.main_loops = {}
        self.rtmp_base = os.getenv("MEDIAMTX_RTMP", "rtmp://localhost:1935")
        
    def start_pipeline(self, stream_id, source_type, source, webrtc_path, ai_processing=False):
        """Start a GStreamer pipeline for a stream"""
        try:
            logger.info(f"Starting pipeline for {stream_id} (AI: {ai_processing})")
            
            # Build pipeline description
            if ai_processing:
                pipeline_desc = self._build_ai_pipeline(source_type, source, webrtc_path)
                # Create AI processor with RTMP output
                rtmp_url = f"{self.rtmp_base}/{webrtc_path}"
                # We'll set dimensions when we get first frame
                self.ai_processors[stream_id] = {
                    'rtmp_url': rtmp_url,
                    'processor': None,  # Will be created when we know dimensions
                    'webrtc_path': webrtc_path
                }
            else:
                pipeline_desc = self._build_passthrough_pipeline(source_type, source, webrtc_path)
            
            logger.info(f"Pipeline description: {pipeline_desc}")
            
            # Create pipeline
            pipeline = Gst.parse_launch(pipeline_desc)
            
            # If AI processing, connect appsink callbacks
            if ai_processing:
                self._setup_ai_callbacks(pipeline, stream_id)
            
            # Set up bus
            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_bus_message, stream_id)
            
            # Start pipeline
            ret = pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                logger.error(f"Failed to start pipeline for {stream_id}")
                return False
            elif ret == Gst.StateChangeReturn.ASYNC:
                logger.info(f"Pipeline {stream_id} state change is ASYNC, waiting for ASYNC_DONE")
            elif ret == Gst.StateChangeReturn.SUCCESS:
                logger.info(f"Pipeline {stream_id} state changed to PLAYING immediately")
            
            self.pipelines[stream_id] = pipeline
            
            # Start GLib main loop in thread
            loop = GLib.MainLoop()
            self.main_loops[stream_id] = loop
            loop_thread = threading.Thread(target=loop.run, daemon=True)
            loop_thread.start()
            
            logger.info(f"Pipeline started successfully for {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            return False
    
    def _build_passthrough_pipeline(self, source_type, source, webrtc_path):
        """Build passthrough pipeline (no AI processing)"""
        
        # Source element
        if source_type == "webcam":
            # V4L2 source for webcam
            source_elem = f"v4l2src device={source}"
        else:
            # RTSP source
            source_elem = f"rtspsrc location={source} latency=100"
        
        # Pipeline: source -> decode -> encode -> RTMP
        pipeline = f"""
        {source_elem} ! 
        decodebin ! 
        videoconvert ! 
        video/x-raw,format=I420 ! 
        clockoverlay time-format="%Y-%m-%d %H:%M:%S" halignment=right valignment=bottom shaded-background=true !
        x264enc bitrate=2000 speed-preset=ultrafast tune=zerolatency ! 
        flvmux streamable=true ! 
        rtmpsink location={self.rtmp_base}/{webrtc_path}
        """
        
        return pipeline.replace('\n', ' ').strip()

    def _build_ai_pipeline(self, source_type, source, webrtc_path):
        """Build AI pipeline with appsink for frame processing"""
        
        # Source element
        if source_type == "webcam":
            source_elem = f"v4l2src device={source}"
        else:
            source_elem = f"rtspsrc location={source} latency=100"
        
        # Simplified pipeline: just decode and send to appsink
        # AI processor will handle encoding and pushing to MediaMTX via ffmpeg
        pipeline = f"""
        {source_elem} !
        decodebin !
        videoconvert ! video/x-raw,format=BGR !
        clockoverlay time-format="%Y-%m-%d %H:%M:%S" halignment=right valignment=bottom shaded-background=true !
        appsink name=ai_sink emit-signals=true max-buffers=1 drop=true sync=false
        """
        
        return pipeline.replace('\n', ' ').strip()
    
    def _setup_ai_callbacks(self, pipeline, stream_id):
        """Set up callbacks for AI processing pipeline"""
        try:
            # Get appsink element
            appsink = pipeline.get_by_name("ai_sink")
            
            if not appsink:
                logger.error(f"Could not find appsink in pipeline for {stream_id}")
                return
            
            # Connect new-sample signal to callback
            appsink.connect("new-sample", self._on_new_sample, stream_id)
            logger.info(f"AI callbacks connected for {stream_id}")
            
        except Exception as e:
            logger.error(f"Error setting up AI callbacks: {e}")
    
    def _on_new_sample(self, appsink, stream_id):
        """Callback when new frame is available from appsink"""
        try:
            # Pull sample from appsink
            sample = appsink.emit("pull-sample")
            if not sample:
                return Gst.FlowReturn.ERROR
            
            # Get buffer and caps
            buf = sample.get_buffer()
            caps = sample.get_caps()
            
            # Get video info from caps
            struct = caps.get_structure(0)
            width = struct.get_value("width")
            height = struct.get_value("height")
            
            # Initialize AI processor if not already done
            ai_info = self.ai_processors.get(stream_id)
            if ai_info and not ai_info['processor']:
                processor = AIProcessor(
                    stream_id=stream_id,
                    rtmp_output=ai_info['rtmp_url'],
                    width=width,
                    height=height,
                    fps=10
                )
                ai_info['processor'] = processor
                logger.info(f"AI processor initialized for {stream_id}: {width}x{height}")
            
            # Map buffer to numpy array
            success, map_info = buf.map(Gst.MapFlags.READ)
            if not success:
                return Gst.FlowReturn.ERROR
            
            # Convert to numpy array (BGR format for OpenCV)
            frame = np.ndarray(
                shape=(height, width, 3),
                dtype=np.uint8,
                buffer=map_info.data
            ).copy()  # Make a copy to safely unmap
            
            buf.unmap(map_info)
            
            # Process frame with AI
            if ai_info and ai_info['processor']:
                ai_info['processor'].process_frame(frame)
            
            return Gst.FlowReturn.OK
            
        except Exception as e:
            logger.error(f"Error in new-sample callback for {stream_id}: {e}", exc_info=True)
            return Gst.FlowReturn.ERROR
    
    
    def stop_pipeline(self, stream_id):
        """Stop a pipeline"""
        try:
            if stream_id in self.pipelines:
                logger.info(f"Stopping pipeline {stream_id}")
                
                pipeline = self.pipelines[stream_id]
                pipeline.set_state(Gst.State.NULL)
                
                # Stop main loop
                if stream_id in self.main_loops:
                    self.main_loops[stream_id].quit()
                    del self.main_loops[stream_id]
                
                # Clean up AI processor
                if stream_id in self.ai_processors:
                    ai_info = self.ai_processors[stream_id]
                    if isinstance(ai_info, dict) and ai_info.get('processor'):
                        ai_info['processor'].cleanup()
                    del self.ai_processors[stream_id]
                    logger.info(f"AI processor cleaned up for {stream_id}")
                
                del self.pipelines[stream_id]
                logger.info(f"Pipeline stopped: {stream_id}")
                
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
    
    def _on_bus_message(self, bus, message, stream_id):
        """Handle GStreamer bus messages"""
        t = message.type
        
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"Pipeline error for {stream_id}: {err}, {debug}")
            self.stop_pipeline(stream_id)
            
        elif t == Gst.MessageType.EOS:
            logger.info(f"End of stream for {stream_id}")
            self.stop_pipeline(stream_id)
        
        elif t == Gst.MessageType.ASYNC_DONE:
            logger.info(f"Pipeline {stream_id} ASYNC_DONE - now in PLAYING state")
            
        elif t == Gst.MessageType.STATE_CHANGED:
            if isinstance(message.src, Gst.Pipeline):
                old_state, new_state, pending_state = message.parse_state_changed()
                logger.info(f"Pipeline {stream_id} state changed: {old_state.value_nick} -> {new_state.value_nick}")
                
        elif t == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            logger.warning(f"Pipeline warning for {stream_id}: {warn}, {debug}")
            
        elif t == Gst.MessageType.INFO:
            info, debug = message.parse_info()
            logger.info(f"Pipeline info for {stream_id}: {info}")
