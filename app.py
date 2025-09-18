import streamlit as st
import yt_dlp

st.title("🎥 YouTube Downloader")

url = st.text_input("Enter YouTube video URL:")

if url:
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        st.success(f"Video title: {info.get('title')}")

        # Filter progressive mp4 formats (video + audio)
        formats = [
            f for f in info['formats']
            if f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') != 'none'
        ]

        if not formats:
            st.warning("No progressive mp4 formats available for this video.")
        else:
            options = [f"{f['format_id']} - {f.get('height', 'N/A')}p" for f in formats]
            choice = st.selectbox("Select format to download:", options)

            if st.button("Download"):
                selected_format_id = choice.split(" - ")[0]
                ydl_opts = {
                    "format": selected_format_id,
                    "outtmpl": "%(title)s.%(ext)s",
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                st.success("Download complete! Check your server's folder.")

    except Exception as e:
        st.error(f"Error: {e}")
