import streamlit as st

st.set_page_config(page_title="Test", layout="wide")
st.title("🚀 Aplikasi Berjalan!")

st.write("Jika kamu melihat ini, Streamlit berfungsi normal.")

# Coba import
try:
    from scrapers import scrape_google_news, scrape_twitter
    from analyzer import cluster_issues, analyze_text
    st.success("Modul berhasil diimport")
except Exception as e:
    st.error(f"Error import: {e}")
