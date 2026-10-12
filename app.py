import streamlit as st
import pandas as pd
import whisper
from deep_translator import GoogleTranslator
import edge_tts
import asyncio
import os
import moviepy.editor as mp

# ១. រៀបចំទំហំ និងឈ្មោះ Web App
st.set_page_config(page_title="AI Video Dubbing", layout="centered")
st.title("🎬 កម្មវិធីបកប្រែ និងបញ្ចូលសំឡេង AI (Khmer Dubbing)")

# ២. កន្លែងសម្រាប់ Upload វីដេអូ
uploaded_file = st.file_uploader("📥 សូមបញ្ចូលវីដេអូទីនេះ (Upload Video)", type=["mp4", "mov"])

if uploaded_file is not None:
    st.video(uploaded_file)

# ៣. ជម្រើសភាសា និងសំឡេង 
col1, col2 = st.columns(2)
with col1:
    target_lang = st.selectbox("Target Language", ["Khmer (Cambodia)"])
with col2:
    voice_option = st.selectbox("Voice", ["km-KH-SreymomNeural (Female)", "km-KH-PisethNeural (Male)"])
    # កំណត់កូដសំឡេងតាមការជ្រើសរើស
    voice_id = "km-KH-SreymomNeural" if "Female" in voice_option else "km-KH-PisethNeural"

# មុខងារ AI សម្រាប់បង្កើតសំឡេង (TTS)
async def generate_tts(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# ៤. ប៊ូតុងបញ្ជា
col3, col4 = st.columns(2)
with col3:
    if st.button("🗑️ Clear", use_container_width=True):
        st.rerun() # សម្រាប់ Refresh វេបសាយឡើងវិញ
        
with col4:
    if st.button("✅ Dubbed (ចាប់ផ្តើមបញ្ចូលសំឡេង)", type="primary", use_container_width=True):
        if uploaded_file is None:
            st.warning("⚠️ សូម Upload វីដេអូជាមុនសិនមុននឹងចុចប៊ូតុងនេះ!")
        else:
            with st.spinner("⏳ កំពុងដំណើរការ AI... (សូមរង់ចាំបន្តិច អាចចំណាយពេលយូរអាស្រ័យលើវីដេអូ)"):
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

                    # ជំហានឃ: បកប្រែជាភាសាខ្មែរ
                    translator = GoogleTranslator(source='auto', target='km')
                    khmer_text = translator.translate(original_text)

                    # បង្ហាញតារាងអត្ថបទ (Transcript Table) នៅលើវេបសាយ
                    st.markdown("### 📝 TRANSCRIPT")
                    data = {"Original": [original_text], "Translated": [khmer_text]}
                    df = pd.DataFrame(data)
                    st.dataframe(df, hide_index=True, use_container_width=True)

                    # ជំហានង: ឱ្យ AI អានសំឡេងខ្មែរ
                    tts_audio_path = "temp_khmer_audio.mp3"
                    asyncio.run(generate_tts(khmer_text, voice_id, tts_audio_path))

                    # ជំហានច: កាត់តបញ្ចូលសំឡេងខ្មែរទៅក្នុងវីដេអូដើមវិញ
                    new_audio = mp.AudioFileClip(tts_audio_path)
                    final_video = video_clip.set_audio(new_audio)
                    final_output_path = "final_dubbed_video.mp4"
                    
                    # បញ្ចេញវីដេអូថ្មី
                    final_video.write_videofile(final_output_path, codec="libx264", audio_codec="aac", logger=None)

                    st.success("🎉 ការបញ្ចូលសំឡេងជោគជ័យ ១០០%! សូមទស្សនាវីដេអូថ្មីរបស់អ្នកនៅខាងក្រោម៖")
                    st.video(final_output_path)

                    # បិទហ្វាល
                    video_clip.close()
                    new_audio.close()
                    final_video.close()
                    
                except Exception as e:
                    st.error(f"❌ មានបញ្ហា: {e}")