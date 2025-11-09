"""
GStreamer pipeline controller with AI integration
Manages passthrough and AI-enabled pipelines
"""
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import logging
import threading

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
        
    def start_pipeline(self, stream_id, source_type, source, webrtc_path, ai_enabled=False):
        """Start a GStreamer pipeline for a stream"""
        try:
            logger.info(f"Starting pipeline for {stream_id} (AI: {ai_enabled})")
            
            # Build pipeline description
            if ai_enabled:
                # pipeline_desc = self._build_ai_pipeline(source_type, source, webrtc_path)
                # # Create AI processor
                # self.ai_processors[stream_id] = AIProcessor(stream_id)
                pass
            else:
                pipeline_desc = self._build_passthrough_pipeline(source_type, source, webrtc_path)
            
            logger.info(f"Pipeline description: {pipeline_desc}")
            
            # Create pipeline
            pipeline = Gst.parse_launch(pipeline_desc)
            
            # Set up bus
            bus = pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_bus_message, stream_id)
            
            # Start pipeline
            ret = pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                logger.error(f"Failed to start pipeline for {stream_id}")
                return False
            
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
        x264enc bitrate=2000 speed-preset=ultrafast tune=zerolatency ! 
        flvmux streamable=true ! 
        rtmpsink location={self.rtmp_base}/{webrtc_path}
        """
        
        return pipeline.replace('\n', ' ').strip()
    
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
            
        elif t == Gst.MessageType.STATE_CHANGED:
            if isinstance(message.src, Gst.Pipeline):
                old_state, new_state, pending_state = message.parse_state_changed()
                logger.info(f"Pipeline {stream_id} state changed: {old_state.value_nick} -> {new_state.value_nick}")
