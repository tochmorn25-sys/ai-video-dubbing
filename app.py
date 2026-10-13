import streamlit as st
import whisper
import os
import subprocess
from openai import OpenAI
import tempfile
import time

st.set_page_config(page_title="AI Subtitle Generator", layout="centered")
st.title("🎬 កម្មវិធីបង្កើត Subtitle ខ្មែរ (.srt)")

api_key = st.text_input("🔑 សូមបញ្ចូល OpenAI API Key របស់អ្នកទីនេះ:", type="password")
uploaded_file = st.file_uploader("📥 សូមបញ្ចូលវីដេអូទីនេះ (Upload Video)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

if st.button("📝 បង្កើត Subtitle ខ្មែរ (.srt)", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ សូមបញ្ចូលកូដសោរ OpenAI API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("⚠️ សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("⏳ កំពុងដំណើរការ AI (សូមរង់ចាំ)..."):
            try:
                client = OpenAI(api_key=api_key)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                    tmp_vid.write(uploaded_file.read())
                    video_path = tmp_vid.name

                audio_path = video_path.replace(".mp4", ".wav")
                
                subprocess.run(["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                segments = result["segments"]

                srt_content = ""
                st.write("កំពុងបកប្រែ...")
                progress_bar = st.progress(0)
                
                for i, segment in enumerate(segments):
                    start_time = format_timestamp(segment["start"])
                    end_time = format_timestamp(segment["end"])
                    original_text = segment["text"]

                    response_trans = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a professional translator. Translate the following text to Khmer. Return ONLY the translated text."},
                            {"role": "user", "content": original_text}
                        ]
                    )
                    khmer_text = response_trans.choices[0].message.content.strip()
                    srt_content += f"{i + 1}\n{start_time} --> {end_time}\n{khmer_text}\n\n"
                    
                    progress_bar.progress((i + 1) / len(segments))
                    time.sleep(0.5)

                st.success("🎉 ការបង្កើត Subtitle ជោគជ័យ!")
                
                st.download_button(
                    label="⬇️ ទាញយកឯកសារ Subtitle (.srt)",
                    data=srt_content,
                    file_name="khmer_subtitle.srt",
                    mime="text/plain",
                    use_container_width=True
                )

                os.remove(video_path)
                os.remove(audio_path)

            except Exception as e:
                st.error(f"❌ មានបញ្ហា: {e}")