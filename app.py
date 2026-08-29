import streamlit as st
import os
import re
import json
import subprocess
import yt_dlp
import whisper
from google import genai

st.set_page_config(page_title="Free AI Shorts Generator", page_icon="🎬", layout="wide")
st.title("🎬 Free AI YouTube Shorts Generator")
st.write("Paste a YouTube link below to automatically generate 9:16 vertical shorts with AI clip ranking!")

st.sidebar.header("🔑 API Settings")
gemini_key = st.sidebar.text_input("Enter Free Gemini API Key:", type="password", help="Get free key from aistudio.google.com")

yt_url = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Generate Shorts Now", type="primary"):
    if not yt_url:
        st.error("Please paste a valid YouTube URL.")
    elif not gemini_key:
        st.error("Please enter your free Google Gemini API Key in the sidebar.")
    else:
        try:
            # 1. Download Video (Bypasses YouTube 403 Forbidden cloud block)
            with st.spinner("1️⃣ Downloading YouTube Video..."):
                if os.path.exists("input_video.mp4"):
                    os.remove("input_video.mp4")
                
                ydl_opts = {
                    'format': 'b[ext=mp4]/best[ext=mp4]/best',
                    'outtmpl': 'input_video.mp4',
                    'overwrites': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web']
                        }
                    }
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([yt_url])
                st.success("✅ Video downloaded successfully!")

            # 2. Transcribe Audio
            with st.spinner("2️⃣ Transcribing Audio with Whisper AI..."):
                model = whisper.load_model("tiny")
                result = model.transcribe("input_video.mp4")
                
                transcript_lines = []
                for seg in result["segments"]:
                    transcript_lines.append(f"[{seg['start']:.2f}s - {seg['end']:.2f}s]: {seg['text'].strip()}")
                full_transcript = "\n".join(transcript_lines)
                st.success("✅ Audio transcribed!")

            # 3. AI Moment Ranking (New official Google GenAI SDK)
            with st.spinner("3️⃣ Gemini AI Analyzing Viral Moments..."):
                client = genai.Client(api_key=gemini_key)
                
                prompt = f"""
                Extract the top 3 most engaging short clip candidates (between 15 to 45 seconds long).
                Return ONLY a valid JSON array of objects with no markdown backticks.
                
                JSON Schema:
                [
                  {{"title": "Catchy Title", "start_time": 10.5, "end_time": 40.0, "reason": "Why engaging"}}
                ]

                Transcript:
                {full_transcript[:12000]}
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                raw_text = response.text.strip()
                
                json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
                clips = json.loads(json_match.group(0)) if json_match else json.loads(raw_text)
                st.success(f"✅ AI identified {len(clips)} viral moments!")

            # 4. Render 9:16 Vertical Shorts
            with st.spinner("4️⃣ Rendering 9:16 Vertical Shorts..."):
                os.makedirs("rendered_shorts", exist_ok=True)
                rendered_files = []
                
                for i, clip in enumerate(clips):
                    start = clip["start_time"]
                    duration = clip["end_time"] - clip["start_time"]
                    clean_title = re.sub(r'[^a-zA-Z0-9]', '_', clip['title']).lower()[:25]
                    out_path = f"rendered_shorts/short_{i+1}_{clean_title}.mp4"
                    
                    ffmpeg_cmd = (
                        f'ffmpeg -y -ss {start} -t {duration} -i input_video.mp4 '
                        f'-vf "crop=ih*(9/16):ih:(iw-ow)/2:0" '
                        f'-c:v libx264 -crf 23 -c:a aac "{out_path}"'
                    )
                    subprocess.run(ffmpeg_cmd, shell=True, check=True)
                    rendered_files.append((clip, out_path))

            st.balloons()
            st.header("🎉 Your Vertical Shorts Are Ready!")

            cols = st.columns(len(rendered_files))
            for idx, (clip, file_path) in enumerate(rendered_files):
                with cols[idx]:
                    st.subheader(f"Short #{idx+1}: {clip['title']}")
                    st.caption(f"💡 {clip['reason']}")
                    st.video(file_path)
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Short",
                            data=f,
                            file_name=os.path.basename(file_path),
                            mime="video/mp4"
                        )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
