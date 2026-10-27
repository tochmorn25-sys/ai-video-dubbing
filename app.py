import streamlit as st
import os
import subprocess
import tempfile
from faster_whisper import WhisperModel
from openai import OpenAI

st.set_page_config(page_title="AI Subtitle Khmer Pro", layout="centered")
st.title("🎬 កម្មវិធីបង្កើត Subtitle ខ្មែរ Pro")

api_key = st.text_input("🔑 OpenAI API Key (បើវីដេអូជាភាសាខ្មែរ មិនចាំបាច់ដាក់ក៏បាន):", type="password")
uploaded_file = st.file_uploader("📥 Upload វីដេអូ", type=["mp4", "mov", "mp3", "wav", "m4a"])

def format_timestamp(seconds: float):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# Load model ម្តងគត់ លឿន
@st.cache_resource
def load_model():
    # small = លឿន, medium = ច្បាស់ជាងសម្រាប់ខ្មែរ
    return WhisperModel("small", device="cpu", compute_type="int8")

if uploaded_file:
    st.video(uploaded_file)

if st.button("📝 បង្កើត Subtitle", type="primary", use_container_width=True):
    if not uploaded_file:
        st.warning("⚠️ សូម Upload វីដេអូសិន!")
    else:
        with st.spinner("⏳ កំពុងស្តាប់ និងចាប់ពេលវេលា..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                    tmp_vid.write(uploaded_file.read())
                    video_path = tmp_vid.name
                audio_path = video_path + ".wav"

                subprocess.run([
                    "ffmpeg", "-y", "-i", video_path,
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", audio_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                model = load_model()
                # vad_filter = សំខាន់ខ្លាំង ធ្វើអោយកាត់សំលេងរំខាន និងចាប់ពេលវេលាត្រូវ
                segments, info = model.transcribe(
                    audio_path, 
                    language="km" if info else None, # auto-detect តែបើដឹងថាខ្មែរ ដាក់ "km" ទៅ
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    beam_size=5,
                    initial_prompt="ជំរាបសួរ សួស្តី ខ្មែរ កម្ពុជា"
                )

                srt_content = ""
                srt_index = 1
                
                # សម្រាប់ប្រមូល text ទាំងអស់ បកប្រែម្ដង (លឿនជាង)
                all_segments = list(segments)
                
                st.write(f"រកឃើញ {len(all_segments)} ប្រយោគ - ភាសា: {info.language}")

                progress = st.progress(0)

                # បើភាសាដើមជាខ្មែរ មិនបាច់បកប្រែ
                is_khmer = info.language == "km"
                client = OpenAI(api_key=api_key) if (api_key and not is_khmer) else None

                for i, seg in enumerate(all_segments):
                    if seg.end - seg.start < 0.3:
                        continue
                    
                    text = seg.text.strip()
                    if not text:
                        continue

                    if not is_khmer and client:
                        # បកប្រែតែបើមិនមែនខ្មែរ
                        res = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Translate to natural, short spoken Khmer. Return only Khmer. If noise, return blank."},
                                {"role": "user", "content": text}
                            ]
                        )
                        text = res.choices[0].message.content.strip()

                    if text:
                        srt_content += f"{srt_index}\n{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n{text}\n\n"
                        srt_index += 1
                    
                    progress.progress((i + 1) / len(all_segments))

                st.success(f"🎉 ជោគជ័យ! បាន {srt_index-1} បន្ទាត់")
                st.text_area("Preview", srt_content, height=350)
                st.download_button("⬇️ ទាញយក khmer.srt", srt_content, "khmer_subtitle.srt", use_container_width=True)

                os.remove(video_path)
                os.remove(audio_path)

            except Exception as e:
                st.error(f"❌ Error: {e}")
