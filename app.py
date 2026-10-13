import streamlit as st
import pandas as pd
import whisper
from gtts import gTTS # ប្ដូរមកប្រើប្រព័ន្ធសំឡេងរបស់ Google វិញ
import os
import moviepy.editor as mp
from openai import OpenAI

# ១. រៀបចំទំហំ និងឈ្មោះ Web App
st.set_page_config(page_title="AI Video Dubbing Pro", layout="centered")
st.title("🎬 កម្មវិធីបកប្រែ និងបញ្ចូលសំឡេង AI (Khmer Dubbing Pro)")

# បន្ថែមកន្លែងដាក់ API Key របស់ OpenAI
api_key = st.text_input("🔑 សូមបញ្ចូល OpenAI API Key របស់អ្នកទីនេះ (ចាប់ផ្តើមដោយ sk-...):", type="password")

# ២. កន្លែងសម្រាប់ Upload វីដេអូ
uploaded_file = st.file_uploader("📥 សូមបញ្ចូលវីដេអូទីនេះ (Upload Video)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)

# ៣. ជម្រើសភាសា និងសំឡេង 
col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Target Language", ["Khmer (Cambodia)"])
with col2:
    voice_option = st.selectbox("Voice", ["Google Standard Voice"])

# ៤. ប៊ូតុងបញ្ជា
col3, col4 = st.columns(2)
with col3:
    if st.button("🗑️ Clear", use_container_width=True):
        st.rerun()
        
with col4:
    if st.button("✅ Dubbed (ចាប់ផ្តើមបញ្ចូលសំឡេង)", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ សូមបញ្ចូលកូដសោរ OpenAI API Key ជាមុនសិន មុននឹងចាប់ផ្តើម!")
        elif uploaded_file is None:
            st.warning("⚠️ សូម Upload វីដេអូជាមុនសិនមុននឹងចុចប៊ូតុងនេះ!")
        else:
            with st.spinner("⏳ កំពុងដំណើរការ AI Pro... (ប្រព័ន្ធដើរលឿនជាងមុន)"):
                try:
                    # ជំហានក: រក្សាទុកវីដេអូដែលបាន Upload
                    video_path = "temp_video.mp4"
                    with open(video_path, "wb") as f:
                        f.write(uploaded_file.read())

                    # ជំហានខ: ទាញយកសំឡេងចេញពីវីដេអូ
                    video_clip = mp.VideoFileClip(video_path)
                    audio_path = "temp_audio.wav"
                    video_clip.audio.write_audiofile(audio_path, logger=None)

                    # ជំហានគ: ស្តាប់ និងទាញយកអក្សរដោយប្រើ Whisper
                    model = whisper.load_model("base")
                    result = model.transcribe(audio_path)
                    original_text = result["text"]

                    # ជំហានឃ: បកប្រែជាភាសាខ្មែរ ដោយប្រើ OpenAI API
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a professional translator. Translate the following text to Khmer (Cambodian). Return ONLY the translated text, without any quotes or extra explanations."},
                            {"role": "user", "content": original_text}
                        ]
                    )
                    khmer_text = response.choices[0].message.content.strip()

                    # បង្ហាញតារាងអត្ថបទ
                    st.markdown("### 📝 TRANSCRIPT")
                    data = {"Original": [original_text], "Translated": [khmer_text]}
                    df = pd.DataFrame(data)
                    st.dataframe(df, hide_index=True, use_container_width=True)

                    # ជំហានង: ឱ្យ AI អានសំឡេងខ្មែរ (ដោយប្រើប្រព័ន្ធ Google TTS)
                    tts_audio_path = "temp_khmer_audio.mp3"
                    tts = gTTS(text=khmer_text, lang='km')
                    tts.save(tts_audio_path)

                    # ជំហានច: កាត់តបញ្ចូលសំឡេងខ្មែរទៅក្នុងវីដេអូដើមវិញ
                    new_audio = mp.AudioFileClip(tts_audio_path)
                    final_video = video_clip.set_audio(new_audio)
                    final_output_path = "final_dubbed_video.mp4"
                    
                    # បញ្ចេញវីដេអូថ្មី
                    final_video.write_videofile(final_output_path, codec="libx264", audio_codec="aac", logger=None)

                    st.success("🎉 ការបញ្ចូលសំឡេងជោគជ័យ ១០០%! ដោយប្រើប្រព័ន្ធ OpenAI Pro!")
                    st.video(final_output_path)

                    # បិទហ្វាល
                    video_clip.close()
                    new_audio.close()
                    final_video.close()
                    
                except Exception as e:
                    st.error(f"❌ មានបញ្ហា: {e}")