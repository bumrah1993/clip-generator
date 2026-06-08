import streamlit as st
import subprocess
import os
import json
import tempfile

st.set_page_config(page_title="🎬 Clip Generator", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0a0a0f; }
    h1, h2, h3 { font-family: 'Space Mono', monospace !important; color: #00ff88 !important; }
    .header-box { background: linear-gradient(135deg, #0d1117, #1a1a2e); border: 1px solid #00ff8833; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; text-align: center; }
    .header-box h1 { font-size: 2.5rem; margin: 0; }
    .header-box p { color: #888; margin: 0.5rem 0 0; }
    .clip-label { font-family: 'Space Mono', monospace; color: #00ff88; font-size: 0.85rem; margin-bottom: 0.5rem; }
    .stButton>button { background: #00ff88 !important; color: #000 !important; font-weight: 700 !important; border: none !important; border-radius: 8px !important; }
    .stDownloadButton>button { background: #1a1a2e !important; color: #00ff88 !important; border: 1px solid #00ff8844 !important; border-radius: 8px !important; }
    .info-box { background: #0d1117; border-left: 3px solid #00ff88; padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; color: #aaa; font-size: 0.9rem; }
    .section-title { color: #00ff88; font-family: 'Space Mono', monospace; font-size: 1.1rem; margin: 1.5rem 0 0.5rem; }
    div[data-testid="stNumberInput"] label { color: #aaa !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
    <h1>🎬 Clip Generator</h1>
    <p>Upload a video → manually select points OR auto-detect with Whisper AI</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    mode = st.radio("Mode", ["✂️ Manual — I pick the points", "🧠 Auto — Whisper AI detects", "⏱️ Auto — Even split"])
    if mode == "🧠 Auto — Whisper AI detects":
        keywords_input = st.text_area("Keywords", value="important, key point, remember, tip, trick, tutorial", height=100)
        clip_duration = st.slider("Clip Duration (seconds)", 15, 60, 30, 5)
        max_clips = st.slider("Max Clips", 1, 10, 5)
    elif mode == "⏱️ Auto — Even split":
        clip_duration = st.slider("Clip Duration (seconds)", 15, 60, 30, 5)
        max_clips = st.slider("Max Clips", 1, 10, 5)
    st.markdown("---")
    st.markdown("<small style='color:#555'>Built by Moksh Shah</small>", unsafe_allow_html=True)

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except:
        return False

def check_whisper():
    try:
        import whisper
        return True
    except:
        return False

if not check_ffmpeg():
    st.error("❌ FFmpeg not found! Please install FFmpeg and add it to PATH.")
    st.stop()

st.markdown("### 📁 Upload Your Video")
uploaded_file = st.file_uploader("Supports MP4, MOV, AVI, MKV", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file:
    # Save to temp for processing
    if "tmp_path" not in st.session_state or st.session_state.get("last_file") != uploaded_file.name:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp.write(uploaded_file.getbuffer())
        tmp.close()
        st.session_state["tmp_path"] = tmp.name
        st.session_state["last_file"] = uploaded_file.name

        # Get duration
        result = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", tmp.name], capture_output=True, text=True)
        info = json.loads(result.stdout)
        st.session_state["duration"] = float(info["format"]["duration"])

    input_path = st.session_state["tmp_path"]
    total_duration = st.session_state["duration"]

    col1, col2 = st.columns([2, 1])
    with col1:
        st.video(uploaded_file)
    with col2:
        st.markdown(f"""
        <div class="info-box">
            <b>File:</b> {uploaded_file.name}<br>
            <b>Size:</b> {round(uploaded_file.size / 1024 / 1024, 2)} MB<br>
            <b>Duration:</b> {int(total_duration // 60)}m {int(total_duration % 60)}s<br>
            <b>Mode:</b> {mode}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── MANUAL MODE ──
    if mode == "✂️ Manual — I pick the points":
        st.markdown('<div class="section-title">✂️ Add Clip Points</div>', unsafe_allow_html=True)
        st.info(f"📽️ Video is **{int(total_duration // 60)}m {int(total_duration % 60)}s** long. Enter start and end times in seconds.")

        if "manual_clips" not in st.session_state:
            st.session_state["manual_clips"] = [{"start": 0.0, "end": 30.0}]

        # Add / Remove clips
        col_add, col_remove = st.columns([1, 1])
        with col_add:
            if st.button("➕ Add Clip Point"):
                last = st.session_state["manual_clips"][-1]
                new_start = min(last["end"], total_duration - 10)
                st.session_state["manual_clips"].append({"start": new_start, "end": min(new_start + 30, total_duration)})
        with col_remove:
            if st.button("➖ Remove Last") and len(st.session_state["manual_clips"]) > 1:
                st.session_state["manual_clips"].pop()

        # Show input for each clip
        for i, clip in enumerate(st.session_state["manual_clips"]):
            st.markdown(f"**Clip {i+1}**")
            c1, c2 = st.columns(2)
            with c1:
                start = st.number_input(f"Start (seconds)", min_value=0.0, max_value=total_duration - 1, value=float(clip["start"]), step=0.5, key=f"start_{i}")
            with c2:
                end = st.number_input(f"End (seconds)", min_value=1.0, max_value=total_duration, value=float(clip["end"]), step=0.5, key=f"end_{i}")
            st.session_state["manual_clips"][i] = {"start": start, "end": end}
            # Show time in human format
            st.caption(f"⏱ {int(start//60)}m {int(start%60)}s → {int(end//60)}m {int(end%60)}s  ({round(end-start, 1)}s clip)")

        timestamps = [(c["start"], c["end"]) for c in st.session_state["manual_clips"]]

        if st.button("🚀 Extract Clips", use_container_width=True):
            _extract = True
        else:
            _extract = False

    # ── WHISPER MODE ──
    elif mode == "🧠 Auto — Whisper AI detects":
        if not check_whisper():
            st.warning("⚠️ Installing openai-whisper...")
            with st.spinner("Installing..."):
                subprocess.run(["py", "-m", "pip", "install", "openai-whisper"], capture_output=True)
            st.rerun()

        timestamps = []
        _extract = False
        if st.button("🚀 Detect & Extract Clips", use_container_width=True):
            keywords = [k.strip().lower() for k in keywords_input.split(",") if k.strip()]
            with st.spinner("🎙️ Transcribing with Whisper AI..."):
                try:
                    import whisper
                    audio_path = input_path.replace(".mp4", "_audio.wav")
                    subprocess.run(["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", "-vn", audio_path], capture_output=True)
                    model = whisper.load_model("base")
                    result = model.transcribe(audio_path, word_timestamps=True)
                    keyword_times = []
                    for segment in result.get("segments", []):
                        text = segment.get("text", "").lower()
                        if any(kw in text for kw in keywords):
                            keyword_times.append(segment["start"])
                    if keyword_times:
                        st.success(f"✅ Found {len(keyword_times)} keyword moments!")
                        seen = set()
                        for t in keyword_times:
                            start = max(0, t - 5)
                            rounded = round(start / 5) * 5
                            if rounded not in seen:
                                seen.add(rounded)
                                end = min(rounded + clip_duration, total_duration)
                                timestamps.append((rounded, end))
                            if len(timestamps) >= max_clips:
                                break
                    else:
                        st.warning("No keywords found. Using even split.")
                except Exception as e:
                    st.warning(f"Whisper error: {e}. Using even split.")

            if not timestamps:
                interval = total_duration / (max_clips + 1)
                for i in range(1, max_clips + 1):
                    start = max(0, round(interval * i - clip_duration / 2, 2))
                    end = min(start + clip_duration, total_duration)
                    if end - start >= 5:
                        timestamps.append((start, end))
            _extract = True

    # ── EVEN SPLIT MODE ──
    else:
        timestamps = []
        _extract = False
        if st.button("🚀 Generate Clips", use_container_width=True):
            interval = total_duration / (max_clips + 1)
            for i in range(1, max_clips + 1):
                start = max(0, round(interval * i - clip_duration / 2, 2))
                end = min(start + clip_duration, total_duration)
                if end - start >= 5:
                    timestamps.append((start, end))
            _extract = True

    # ── EXTRACT ──
    if _extract and timestamps:
        output_dir = tempfile.mkdtemp()
        st.markdown("### ✂️ Extracting Clips...")
        progress = st.progress(0)
        clip_files = []

        for i, (start, end) in enumerate(timestamps):
            if end <= start:
                st.warning(f"⚠️ Clip {i+1} skipped — end time must be greater than start time.")
                continue
            clip_name = f"clip_{i+1}_{int(start)}s-{int(end)}s.mp4"
            clip_path = os.path.join(output_dir, clip_name)
            subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-preset", "fast", "-crf", "23", clip_path], capture_output=True)
            if os.path.exists(clip_path) and os.path.getsize(clip_path) > 0:
                with open(clip_path, "rb") as f:
                    clip_bytes = f.read()
                clip_files.append((clip_name, clip_bytes, start, end))
            progress.progress((i + 1) / len(timestamps))

        if clip_files:
            st.markdown(f"### 🎞️ {len(clip_files)} Clips Ready!")
            cols = st.columns(2)
            for idx, (clip_name, clip_bytes, start, end) in enumerate(clip_files):
                with cols[idx % 2]:
                    st.markdown(f'<div class="clip-label">📌 Clip {idx+1} — {int(start//60)}m{int(start%60)}s → {int(end//60)}m{int(end%60)}s</div>', unsafe_allow_html=True)
                    st.video(clip_bytes)
                    st.download_button(f"⬇️ Download Clip {idx+1}", data=clip_bytes, file_name=clip_name, mime="video/mp4", key=f"dl_{idx}")
        else:
            st.error("❌ No clips were extracted. Check your time inputs.")
