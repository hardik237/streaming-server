"""
Streamlit UI - Index Page
Stream source selection (WebCam or IP Camera)
"""
import streamlit as st
import utils.api_client as api_client

print("UI App - Index Page Loaded")

st.set_page_config(page_title="Live Streaming Solution", page_icon="📹", layout="wide")
st.title("Live Video Streaming Solution")
st.markdown("---")

# Source selection
st.subheader("Select Video Source")
source_type = st.radio("Source Type:", ["WebCam", "IP Camera (RTSP)"], horizontal=True)
stream_id = st.text_input("Stream ID:", value="cam_1", placeholder="e.g., Test_cam_1")

if source_type == "WebCam":
    # Simple device selection - can be enhanced to list available devices
    device = st.selectbox("Select Device:", ["/dev/video0", "/dev/video1", "/dev/video2"])
    source = device
elif source_type == "IP Camera (RTSP)":
    rtsp_url = st.text_input(
        "RTSP URL:", 
        value="rtsp://mediamtx-rtsp-server:9554/person",
        placeholder="rtsp://mediamtx-rtsp-server:9554/person",
        help="Enter the complete RTSP URL including credentials if needed"
    )
    source = rtsp_url

# Create stream button
# col1, col2, col3 = st.columns([1, 2, 1])
    
if st.button("Add Stream", type="primary", use_container_width=True):
    if stream_id == "":
        st.error("Please enter a Stream ID")
    
    if source_type == "IP Camera (RTSP)" and not rtsp_url:
        st.error("Please enter an RTSP URL")
    else:
        with st.spinner("Starting stream..."):
            try:
                
                # Create stream via API
                response = api_client.create_stream(
                    stream_id=stream_id,
                    source_type="webcam" if source_type == "WebCam" else "rtsp",
                    source=source,
                )
                
                print("Create Stream Response:", response)
                
                if response and response.get("status") == "live":
                    st.success(f"Stream started successfully!")
                    st.info(f"Stream ID: {stream_id}")
                else:
                    st.error(f"Failed to start stream: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()

try:
    streams = api_client.get_all_streams()
    
    # create a table view
    # Define your column headers and widths
    headers = ["ID", "Type", "Source", "Status", "WebRTC", "Stop", "Restart", "Delete"]
    col_widths = [1, 1, 2, 1, 1, 1, 1, 1]  # Adjust widths as needed

    # Create columns dynamically
    cols = st.columns(col_widths, border=True)
    # Write headers dynamically
    for col, header in zip(cols, headers):
        col.write(f"**{header}**")
        col.write("---")
    
    if streams and isinstance(streams, list):
        for stream in streams:
            with cols[0]:
                st.write(stream.get("stream_id", ""))
            with cols[1]:
                st.write(stream.get("source_type", "`"))
            with cols[2]:
                source = stream.get("source_spec", {}).get("device") if stream.get("source_type") == "webcam" else stream.get("source_spec", {}).get("rtsp_url", "")
                st.write(source)
            with cols[3]:
                if stream.get("status", "") == "live":
                    st.write(f"🟢 {stream.get('status', '')}")
                else:
                    st.write(f"🔴 {stream.get('status', '')}")
            with cols[4]:
                webrtc_path = stream.get('webrtc_path', '')
                st.link_button("▶️", url=f"http://localhost:8889/{webrtc_path}", type="secondary", use_container_width=False)
            with cols[5]:
                st.button("🛑", key=f"stop_{stream.get('stream_id', '')}", on_click=lambda sid=stream.get("stream_id", ""): api_client.stop_stream(sid))
            with cols[6]:
                st.button("🔄", key=f"restart_{stream.get('stream_id', '')}", on_click=lambda sid=stream.get("stream_id", ""): api_client.restart_stream(sid))
            with cols[7]:
                st.button("🗑️", key=f"delete_{stream.get('stream_id', '')}", on_click=lambda sid=stream.get("stream_id", ""): api_client.delete_stream(sid))

except Exception as e:
    st.warning(f"Could not load active streams: {str(e)}")
    
st.divider()

st.button("Stop All Streams", type="primary", use_container_width=True, on_click=api_client.stop_all_streams)
st.button("Flush Database", type="primary", use_container_width=True, on_click=api_client.flush_db)

st.divider()

st.header("Instructions")
st.markdown("""
1. **WebCam**: Select your local webcam device
2. **IP Camera**: Enter the RTSP URL of your IP camera
3. Click **Start Streaming** to begin
4. You'll be redirected to the live view page with playback controls
""")




