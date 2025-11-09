import datetime
import streamlit as st
import utils.api_client as api_client
from utils.utils import convert_to_iso_standard, get_system_ip_address
import time

st.set_page_config(page_title="Playback", page_icon="📹", layout="wide")
st.title("Playback Recorded Streams")
st.divider()

print("UI App - Playback Page Loaded")

try:
    streams = api_client.get_all_streams()
    
    # create a table view
    # Define your column headers and widths
    st.info("Right now, records are only for 24 hours only")
    
    # Initialize default times in session state if not present
    if 'default_start_time' not in st.session_state:
        st.session_state.default_start_time = (datetime.datetime.now() - datetime.timedelta(minutes=5)).time()
    if 'default_end_time' not in st.session_state:
        st.session_state.default_end_time = datetime.datetime.now().time()
    
    # Use a form to prevent page reload on each input change
    with st.form("recording_form"):
        headers = ["ID", "Start Time", "End Time"]
        col_widths = [1, 2, 2]  # Adjust widths as needed

        # Create columns dynamically inside the form
        cols = st.columns(col_widths, border=True)
        # Write headers dynamically
        for col, header in zip(cols, headers):
            col.write(f"**{header}**")
            col.write("---")
        
        with cols[0]:
            selected_stream = st.selectbox("Select Stream", options=[stream.get("stream_id", "") for stream in streams], key="playback_stream_select")
        with cols[1]:
            start_time = st.time_input("Start Time", value=st.session_state.default_start_time, step=120)
        with cols[2]:
            end_time = st.time_input("End Time", value=st.session_state.default_end_time, step=120)
        
        submitted = st.form_submit_button("Get Recordings", type="primary", use_container_width=True)
    
    if submitted:
        if end_time <= start_time:
            st.error("End Time must be after Start Time")
        elif not selected_stream:
            st.error("Please select a stream")
        else:
            with st.spinner("Fetching recordings..."):
                try:
                    recordings = api_client.get_recordings(
                        stream_id=selected_stream,
                        start_time=convert_to_iso_standard(start_time),
                        end_time=convert_to_iso_standard(end_time)
                    )
                    
                    # st.write(recordings)
                    
                    if "error" in recordings:
                        time.sleep(5)
                        raise Exception("No recordings found, try again later")
                    else:
                        got_recordings = True
                    
                    record = recordings[0] if recordings else None
                    if record:
                        st.success(f"Found {len(recordings)} recordings")
                        playback_url = record.get("url", "")
                        playback_url = playback_url.replace("http://localhost", f"http://{get_system_ip_address()}")
                        st.video(playback_url, autoplay=True, width=700)
                    
                except Exception as e:
                    st.info(f"{str(e)}")

except Exception as e:
    st.warning(f"Could not load active streams: {str(e)}")
    
st.divider()