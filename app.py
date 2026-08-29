import streamlit as st
import os
import re
import json
import subprocess
import yt_dlp
import whisper
from google import genai

st.set_page_config(page_title="Free AI Shorts Generator with Captions", page_icon="🎬", layout="wide")
st.title("🎬 Free AI Shorts Generator (With Bold Captions & Virality Ranking)")
st.write("Extract 7-8 viral shorts (60s-90s long) with bold yellow captions burned onto vertical 9:16 videos!")

# Sidebar Settings
st.sidebar.header("🔑 API Settings")
gemini_key = st.sidebar.text_input("Enter Free Gemini API Key:", type="password", help="Get free key from aistudio.google.com")

tab1, tab2 = st.tabs(["🔗 YouTube Link", "📁 Upload Video File"])

yt_url = ""
uploaded_file = None

with tab1:
    yt_url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

with tab2:
    uploaded_file = st.file_uploader("Upload an MP4 or MOV video file:", type=["mp4", "mov", "mkv"])

# Robust YouTube Downloader with TV Player Client Fallback (Bypasses Bot Verification)
def download_youtube_video(url, output_path="input_video.mp4"):
    client_strategies = [
        ['tv', 'mweb'],
        ['ios', 'android'],
        ['web', 'mweb']
    ]
    last_err = None
    for clients in client_strategies:
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            
            ydl_opts = {
                'format': 'b[ext=mp4]/best[ext=mp4]/best',
                'outtmpl': output_path,
                'overwrites': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': clients
                    }
                },
                'nocheckcertificate': True,
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except Exception as e:
            last_err = e
            continue
            
    if last_err:
        raise last_err
    return False

# Helper function to generate ASS Subtitles with Bold Yellow styling
def format_time_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def create_ass_subtitles(whisper_segments, clip_start, clip_end, output_ass_path):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,65,&H0000FFFF,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogues = []
    for seg in whisper_segments:
        s_start = seg["start"]
        s_end = seg["end"]
        
        if s_end > clip_start and s_start < clip_end:
            rel_start = max(0.0, s_start - clip_start)
            rel_end = min(clip_end - clip_start, s_end - clip_start)
            
            t_start = format_time_ass(rel_start)
            t_end = format_time_ass(rel_end)
            text = seg["text"].strip().upper()
            
            # Format text into short 3-4 word lines for punchy mobile captions
            words = text.split()
            lines = []
            for k in range(0, len(words), 4):
                lines.append(" ".join(words[k:k+4]))
            formatted_text = "\\N".join(lines)
            
            dialogues.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{formatted_text}")

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(dialogues))

if st.button("🚀 Generate 7-8 Viral Shorts Now", type="primary"):
    if not yt_url and not uploaded_file:
        st.error("Please paste a YouTube URL or upload a video file.")
    elif not gemini_key:
        st.error("Please enter your free Google Gemini API Key in the sidebar.")
    else:
        try:
            # Step 1: Download / Save Video
            if uploaded_file is not None:
                with st.spinner("1️⃣ Saving uploaded video file..."):
                    with open("input_video.mp4", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success("✅ Video file ready!")
            else:
                with st.spinner("1️⃣ Downloading YouTube Video..."):
                    download_youtube_video(yt_url, "input_video.mp4")
                    st.success("✅ Video downloaded!")

            # Step 2: Transcribe Audio with Timestamps
            with st.spinner("2️⃣ Transcribing Audio & Extracting Subtitles with Whisper AI..."):
                model = whisper.load_model("tiny")
                result = model.transcribe("input_video.mp4")
                whisper_segments = result["segments"]
                
                transcript_lines = []
                for seg in whisper_segments:
                    transcript_lines.append(f"[{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text'].strip()}")
                full_transcript = "\n".join(transcript_lines)
                st.success(f"✅ Transcribed {len(whisper_segments)} audio segments!")

            # Step 3: Gemini AI Virality Analysis (7 to 8 clips, 60s to 90s long)
            with st.spinner("3️⃣ Gemini AI Scoring & Extracting Top 7-8 Viral Moments (60s - 90s long)..."):
                client = genai.Client(api_key=gemini_key)
                
                prompt = f"""
                You are a YouTube Shorts & TikTok virality expert.
                Analyze this video transcript and extract the top 7 to 8 MOST VIRAL clip candidates.
                Each clip MUST be between 60 seconds and 90 seconds long (duration = 60s to 90s).
                
                Assign a virality score from 1 to 100 for each clip based on hook strength, emotional impact, and retention.
                Order the clips from HIGHEST virality score to lowest.
                
                Return ONLY a valid JSON array of objects without markdown backticks.
                JSON Schema:
                [
                  {{
                    "title": "Viral Catchy Title",
                    "start_time": 12.0,
                    "end_time": 75.0,
                    "virality_score": 95,
                    "reason": "Strong hook, controversial statement, high engagement potential"
                  }}
                ]

                Transcript:
                {full_transcript[:25000]}
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                raw_text = response.text.strip()
                
                json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                clips = json.loads(json_match.group(0)) if json_match else json.loads(raw_text)
                
                # Sort by virality score
                clips.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
                st.success(f"✅ AI found and ranked {len(clips)} viral shorts (60s-90s long)!")

            # Step 4: Render Vertical 9:16 Shorts with BOLD Yellow Captions
            with st.spinner("4️⃣ Rendering 9:16 Vertical Videos with BOLD Yellow Captions..."):
                os.makedirs("rendered_shorts", exist_ok=True)
                rendered_files = []
                
                for i, clip in enumerate(clips):
                    start = clip["start_time"]
                    end = clip["end_time"]
                    duration = end - start
                    clean_title = re.sub(r'[^a-zA-Z0-9]', '_', clip['title']).lower()[:25]
                    
                    sub_file = f"rendered_shorts/sub_{i+1}.ass"
                    out_path = f"rendered_shorts/short_{i+1}_{clean_title}.mp4"
                    
                    # Generate ASS Subtitle File
                    create_ass_subtitles(whisper_segments, start, end, sub_file)
                    
                    # FFmpeg command: crop 9:16 + burn bold ASS subtitles
                    ffmpeg_cmd = (
                        f'ffmpeg -y -ss {start} -t {duration} -i input_video.mp4 '
                        f'-vf "crop=ih*(9/16):ih:(iw-ow)/2:0,subtitles={sub_file}" '
                        f'-c:v libx264 -crf 22 -c:a aac "{out_path}"'
                    )
                    subprocess.run(ffmpeg_cmd, shell=True, check=True)
                    rendered_files.append((clip, out_path))

            st.balloons()
            st.header("🎉 Your Ranked Viral Shorts with Bold Captions Are Ready!")

            # Display Videos
            for idx, (clip, file_path) in enumerate(rendered_files):
                st.markdown("---")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.video(file_path)
                with c2:
                    score = clip.get('virality_score', 'N/A')
                    st.subheader(f"🔥 Short #{idx+1}: {clip['title']}")
                    st.markdown(f"**Virality Score:** 🔥 `{score}/100`")
                    st.markdown(f"**Duration:** ⏱️ `{clip['end_time'] - clip['start_time']:.1f}s` (Range: {clip['start_time']}s - {clip['end_time']}s)")
                    st.write(f"**Why Viral:** {clip['reason']}")
                    
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"📥 Download Short #{idx+1}",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime="video/mp4",
                            key=f"dl_{idx}"
                        )

        except Exception as e:
            err_msg = str(e)
            if "DRM protected" in err_msg or "confirm you're not a bot" in err_msg:
                st.error("⚠️ YouTube bot verification block for this URL. Please use the 'Upload Video File' tab to upload your MP4 file directly!")
            else:
                st.error(f"An error occurred: {err_msg}")
