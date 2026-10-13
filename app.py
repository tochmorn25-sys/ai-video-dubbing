import streamlit as st
import pandas as pd
import whisper
import os
import subprocess
from openai import OpenAI

st.set_page_config(page_title="AI Video Dubbing Pro", layout="centered")
st.title("🎬 កម្មវិធីបកប្រែ និងបញ្ចូលសំឡេង AI (OpenAI VIP)")

api_key = st.text_input("🔑 សូមបញ្ចូល OpenAI API Key របស់អ្នកទីនេះ:", type="password")
uploaded_file = st.file_uploader("📥 សូមបញ្ចូលវីដេអូទីនេះ (Upload Video)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)

col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Target Language", ["Khmer (Cambodia)"])
with col2:
    voice_option = st.selectbox("Voice", ["OpenAI VIP Voice (Nova)"]) 

if st.button("✅ Dubbed (ចាប់ផ្តើមបញ្ចូលសំឡេង)", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ សូមបញ្ចូលកូដសោរ OpenAI API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("⚠️ សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("⏳ កំពុងដំណើរការ AI VIP (សូមរង់ចាំបន្តិចសម្រាប់វីដេអូវែង)..."):
            try:
                client = OpenAI(api_key=api_key)

                # ក. រក្សាទុកវីដេអូ
                video_path = "temp_video.mp4"
                with open(video_path, "wb") as f:
                    f.write(uploaded_file.read())

                # ខ. ទាញសំឡេងចេញ
                audio_path = "temp_audio.wav"
                subprocess.run(["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # គ. ស្តាប់អក្សរ
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                original_text = result["text"]

                # ឃ. បកប្រែ 
                response_trans = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional translator. Translate the following text to Khmer. Return ONLY the translated text."},
                        {"role": "user", "content": original_text}
                    ]
                )
                khmer_text = response_trans.choices[0].message.content.strip()

                st.markdown("### 📝 TRANSCRIPT")
                st.dataframe(pd.DataFrame({"Original": [original_text], "Translated": [khmer_text]}), hide_index=True, use_container_width=True)

                # ង. បង្កើតសំឡេងដោយប្រើ OpenAI TTS (Premium ធានាមិនគាំង)
                tts_audio_path = "temp_khmer_audio.mp3"
                response_tts = client.audio.speech.create(
                    model="tts-1",
                    voice="nova", # សំឡេងស្រីរបស់ OpenAI
                    input=khmer_text[:4000] # ការពារកុំឱ្យលើសកំណត់
                )
                response_tts.stream_to_file(tts_audio_path)

                # ច. លាយសំឡេងចូលគ្នា
                final_output_path = "final_dubbed_video.mp4"
                merge_cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", tts_audio_path,
                    "-filter_complex", "[0:a]volume=0.15[a1];[1:a]volume=1.5[a2];[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]",
                    "-map", "0:v",
                    "-map", "[a]",
                    "-c:v", "copy", 
                    "-c:a", "aac",
                    final_output_path
                ]
                subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                st.success("🎉 ជោគជ័យ ១០០%! App ដើរដោយថាមពល OpenAI VIP ដាច់កូដ Block ទាំងស្រុង!")
                st.video(final_output_path)
                
            except Exception as e:
                st.error(f"❌ មានបញ្ហា: {e}")