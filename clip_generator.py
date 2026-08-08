import streamlit as st
import subprocess
import os
import json
import tempfile

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

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
    <p style="margin-top:1rem; font-size:1.1rem; color:#00ff88; font-family:'Space Mono',monospace; letter-spacing:2px;"></p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    mode = st.radio("Mode", ["✂️ Manual — I pick the points", "🧠 Auto — Whisper AI detects", "⏱️ Auto — Even split"])
    if mode == "🧠 Auto — Whisper AI detects":
        keywords_input = st.text_area("Keywords", value="important, key point, remember, tip, trick, tutorial", height=100)
        clip_duration = st.slider("Clip Duration (seconds)", 5, 60, 30, 5)
        max_clips = st.slider("Max Clips", 1, 10, 5)
    elif mode == "⏱️ Auto — Even split":
        clip_duration = st.slider("Clip Duration (seconds)", 5, 60, 30, 5)
        max_clips = st.slider("Max Clips", 1, 10, 5)
    st.markdown("---")
    st.markdown("<small style='color:#555'>Built by Moksh Shah</small>", unsafe_allow_html=True)

def get_ffmpeg_binary():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return "ffmpeg"
    except Exception:
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

def get_ffprobe_binary():
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        return "ffprobe"
    except Exception:
        ffmpeg_exe = get_ffmpeg_binary()
        ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
        if os.path.exists(ffprobe_exe):
            return ffprobe_exe
        return "ffprobe"

def check_ffmpeg():
    try:
        ffmpeg_bin = get_ffmpeg_binary()
        subprocess.run([ffmpeg_bin, "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False

def check_whisper():
    try:
        import whisper
        return True
    except Exception:
        return False

if not check_ffmpeg():
    st.error("❌ FFmpeg not found! Please install FFmpeg and add it to PATH.")
    st.stop()

def get_video_duration(path):
    try:
        ffmpeg_bin = get_ffmpeg_binary()
        result = subprocess.run([ffmpeg_bin, "-i", path], capture_output=True, text=True)
        import re
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
        if match:
            hours, mins, secs = match.groups()
            dur = float(hours) * 3600 + float(mins) * 60 + float(secs)
            if dur > 0:
                return dur
    except Exception:
        pass

    try:
        ffprobe_bin = get_ffprobe_binary()
        result = subprocess.run([ffprobe_bin, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], capture_output=True, text=True)
        val = result.stdout.strip()
        if val:
            dur = float(val)
            if dur > 0:
                return dur
    except Exception:
        pass

    return 180.0

st.markdown("### 📁 Upload Your Video")
uploaded_file = st.file_uploader("Supports MP4, MOV, AVI, MKV", type=["mp4", "mov", "avi", "mkv"])

if uploaded_file:
    # Save to temp and calculate duration on any new file upload
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if "file_id" not in st.session_state or st.session_state.get("file_id") != file_id or "duration" not in st.session_state:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp.write(uploaded_file.getbuffer())
        tmp.close()
        st.session_state["tmp_path"] = tmp.name
        st.session_state["file_id"] = file_id
        st.session_state["duration"] = get_video_duration(tmp.name)

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
            st.session_state["manual_clips"] = [{"start": 0.0, "end": min(30.0, total_duration)}]

        # Add / Remove clips
        col_add, col_remove = st.columns([1, 1])
        with col_add:
            if st.button("➕ Add Clip Point"):
                last = st.session_state["manual_clips"][-1]
                new_start = min(last["end"], max(0.0, total_duration - 1.0))
                st.session_state["manual_clips"].append({"start": new_start, "end": min(new_start + 30.0, total_duration)})
        with col_remove:
            if st.button("➖ Remove Last") and len(st.session_state["manual_clips"]) > 1:
                st.session_state["manual_clips"].pop()

        # Show input for each clip
        for i, clip in enumerate(st.session_state["manual_clips"]):
            st.markdown(f"**Clip {i+1}**")
            c1, c2 = st.columns(2)
            max_start = max(0.0, total_duration - 0.5)
            val_start = min(max(0.0, float(clip["start"])), max_start)
            val_end = min(max(0.5, float(clip["end"])), total_duration)
            if val_end <= val_start:
                val_end = min(val_start + 5.0, total_duration)

            with c1:
                start = st.number_input(f"Start (seconds)", min_value=0.0, max_value=max_start, value=val_start, step=0.5, key=f"start_{i}")
            with c2:
                end = st.number_input(f"End (seconds)", min_value=0.1, max_value=total_duration, value=val_end, step=0.5, key=f"end_{i}")
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
            if not keywords:
                mode = "⏱️ Auto — Even split"
            with st.spinner("🎙️ Transcribing with Whisper AI..."):
                try:
                    import whisper
                    ffmpeg_bin = get_ffmpeg_binary()
                    audio_path = input_path.replace(".mp4", "_audio.wav")
                    subprocess.run([ffmpeg_bin, "-y", "-i", input_path, "-ar", "16000", "-ac", "1", "-vn", audio_path], capture_output=True)
                    model = whisper.load_model("base")
                    result = model.transcribe(audio_path, word_timestamps=True)
                    keyword_matches = []
                    for segment in result.get("segments", []):
                        seg_text = segment.get("text", "").lower()
                        words = segment.get("words", [])

                        found_in_segment = False
                        if words:
                            for w in words:
                                w_text = w.get("word", "").lower().strip(".,!?;:\"' ")
                                for kw in keywords:
                                    if kw in w_text:
                                        w_start = w.get("start", segment.get("start", 0.0))
                                        keyword_matches.append((w_start, kw))
                                        found_in_segment = True
                                        break

                        if not found_in_segment:
                            for kw in keywords:
                                idx = seg_text.find(kw)
                                if idx != -1:
                                    seg_start = segment.get("start", 0.0)
                                    seg_end = segment.get("end", seg_start + 5.0)
                                    ratio = idx / max(1, len(seg_text))
                                    est_start = seg_start + (seg_end - seg_start) * ratio
                                    keyword_matches.append((est_start, kw))
                                    break

                    if keyword_matches:
                        st.success(f"✅ Found {len(keyword_matches)} keyword moment(s)!")
                        seen = []
                        for t, kw in keyword_matches:
                            start = max(0.0, round(t, 2))
                            if not any(abs(start - s) < 3.0 for s in seen):
                                seen.append(start)
                                end = min(start + clip_duration, total_duration)
                                timestamps.append((start, end))
                                st.info(f"📍 Keyword '{kw}' detected → Clip starts exactly at {int(start//60)}m {round(start%60, 1)}s")
                            if len(timestamps) >= max_clips:
                                break
                    else:
                        st.warning("⚠️ No matching keywords found in transcript.")
                except Exception as e:
                    st.warning(f"Whisper error: {e}. Using even split.")

            if not timestamps:
                num_clips = max_clips
                eff_dur = min(clip_duration, total_duration)
                if num_clips == 1:
                    timestamps = [(0.0, eff_dur)]
                else:
                    max_start = max(0.0, total_duration - eff_dur)
                    step = max_start / (num_clips - 1) if max_start > 0 else 0.0
                    for i in range(num_clips):
                        start = round(i * step, 2)
                        end = round(min(start + eff_dur, total_duration), 2)
                        timestamps.append((start, end))
            _extract = True

    # ── EVEN SPLIT MODE ──
    else:
        timestamps = []
        _extract = False
        if st.button("🚀 Generate Clips", use_container_width=True):
            num_clips = max_clips
            eff_dur = min(clip_duration, total_duration)
            if num_clips == 1:
                timestamps = [(0.0, eff_dur)]
            else:
                max_start = max(0.0, total_duration - eff_dur)
                step = max_start / (num_clips - 1) if max_start > 0 else 0.0
                for i in range(num_clips):
                    start = round(i * step, 2)
                    end = round(min(start + eff_dur, total_duration), 2)
                    timestamps.append((start, end))

            if timestamps:
                st.success(f"✅ Generated all {len(timestamps)} clips of {int(eff_dur)}s each!")
            _extract = True

    # ── EXTRACT ──
    if _extract and timestamps:
        output_dir = tempfile.mkdtemp()
        st.markdown("### ✂️ Extracting Clips...")
        progress = st.progress(0)
        clip_files = []
        ffmpeg_bin = get_ffmpeg_binary()

        for i, (start, end) in enumerate(timestamps):
            if start >= total_duration:
                break
            actual_end = min(end, total_duration)
            clip_dur = actual_end - start
            if clip_dur < 1.0:
                continue

            clip_name = f"clip_{i+1}_{int(start)}s-{int(actual_end)}s.mp4"
            clip_path = os.path.join(output_dir, clip_name)
            subprocess.run([
                ffmpeg_bin, "-y",
                "-ss", str(start),
                "-i", input_path,
                "-t", str(clip_dur),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-preset", "fast",
                "-crf", "23",
                clip_path
            ], capture_output=True)

            if os.path.exists(clip_path) and os.path.getsize(clip_path) > 5000:
                with open(clip_path, "rb") as f:
                    clip_bytes = f.read()
                clip_files.append((clip_name, clip_bytes, start, actual_end))
            progress.progress((i + 1) / len(timestamps))

        if clip_files:
            st.markdown(f"### 🎞️ {len(clip_files)} Clips Ready!")
            if mode != "✂️ Manual — I pick the points" and len(clip_files) < max_clips:
                st.info(f"ℹ️ {len(clip_files)} valid clips were generated out of {max_clips} requested based on total video length ({int(total_duration // 60)}m {int(total_duration % 60)}s).")
            cols = st.columns(2)
            for idx, (clip_name, clip_bytes, start, end) in enumerate(clip_files):
                with cols[idx % 2]:
                    st.markdown(f'<div class="clip-label">📌 Clip {idx+1} — {int(start//60)}m{int(start%60)}s → {int(end//60)}m{int(end%60)}s</div>', unsafe_allow_html=True)
                    st.video(clip_bytes)
                    st.download_button(f"⬇️ Download Clip {idx+1}", data=clip_bytes, file_name=clip_name, mime="video/mp4", key=f"dl_{idx}")
        else:
            st.error("❌ No valid clips could be extracted. Please check your time inputs and video format.")
