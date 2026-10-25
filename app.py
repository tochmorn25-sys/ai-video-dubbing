import streamlit as st
import whisper
import os
import subprocess
from openai import OpenAI
import tempfile
import time

st.set_page_config(page_title="AI Subtitle Generator", layout="centered")
st.title("🎬 កម្មវិធីបង្កើត Subtitle ខ្មែរ (Pro Version)")

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
        with st.spinner("⏳ កំពុងដំណើរការ AI ម៉ូដែលថ្មី (អាចចំណាយពេលយូរជាងមុនបន្តិច)..."):
            try:
                client = OpenAI(api_key=api_key)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_vid:
                    tmp_vid.write(uploaded_file.read())
                    video_path = tmp_vid.name

                audio_path = video_path.replace(".mp4", ".wav")
                
                # បង្កើនគុណភាពសំឡេងមុននឹងឱ្យ Whisper ស្តាប់
                subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # ប្តូរពីម៉ូដែល "base" ទៅ "small" ដើម្បីឱ្យវាស្តាប់បានច្បាស់ជាងមុន (ចំណាយពេលយូរជាងមុនបន្តិច តែលទ្ធផលល្អជាង)
                model = whisper.load_model("medium")
                
                # កំណត់លក្ខខណ្ឌឱ្យ Whisper ដើម្បីកាត់បន្ថយការចាប់សំឡេងអត់ន័យ
                result = model.transcribe(audio_pa)
                segments = result["segments"]

                srt_content = ""
                st.write("កំពុងបកប្រែ និងរៀបចំអត្ថបទ...")
                progress_bar = st.progress(0)
                
                srt_index = 1 
                
                for i, segment in enumerate(segments):
                    start_time = format_timestamp(segment["start"])
                    end_time = format_timestamp(segment["end"])
                    original_text = segment["text"].strip()

                    # លក្ខខណ្ឌកាត់ចោលភ្លាមៗ បើអក្សរដើមខ្លីពេក ឬគ្មានអត្ថន័យ
                    if len(original_text) < 2 or original_text in ["♪", "...", "(sigh)", "(groans)"]:
                        continue

                    response_trans = client.chat.completions.create(
                        model="gpt-4o", # ប្តូរទៅប្រើម៉ូដែល GPT-4o ធំតែម្ដង ដើម្បីបកប្រែបានឆ្លាត និងរលូនជាង
                        messages=[
                            {"role": "system", "content": """You are an expert movie subtitle translator. 
                            1. Translate the provided text into natural, spoken Khmer (Cambodian). 
                            2. CRITICAL: Your output MUST contain ONLY Khmer script. ABSOLUTELY NO Chinese characters, NO English words, NO symbols (like ♪).
                            3. If the input text seems to be just a sound effect (like sighing, moaning, laughing) or doesn't make logical sense as a spoken sentence, DO NOT translate it. Just output the word 'SKIP'.
                            4. Do not apologize or explain."""},
                            {"role": "user", "content": original_text}
                        ]
                    )
                    khmer_text = response_trans.choices[0].message.content.strip()
                    
                    # ពិនិត្យមើលថាបើ AI ប្រាប់ឱ្យ SKIP គឺយើងរំលងចោល
                    if khmer_text != "SKIP" and khmer_text != "":
                         # លុបអក្សរចិនចេញក្រែងលោវានៅសល់
                         import re
                         khmer_text = re.sub(r'[\u4e00-\u9fff]+', '', khmer_text).strip()
                         
                         if len(khmer_text) > 1:
                             srt_content += f"{srt_index}\n{start_time} --> {end_time}\n{khmer_text}\n\n"
                             srt_index += 1
                    
                    progress_bar.progress((i + 1) / len(segments))
                    time.sleep(0.5)

                st.success("🎉 ការបង្កើត Subtitle រួចរាល់ដោយជោគជ័យ!")
                
                st.download_button(
                    label="⬇️ ទាញយកឯកសារ Subtitle (.srt)",
                    data=srt_content,
                    file_name="khmer_subtitle_pro.srt",
                    mime="text/plain",
                    use_container_width=True
                )

                os.remove(video_path)
                os.remove(audio_path)

            except Exception as e:
                st.error(f"❌ មានបញ្ហា: {e}")
