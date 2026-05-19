import streamlit as st
import pandas as pd
from scrapers import scrape_google_news, scrape_twitter
from analyzer import cluster_issues, analyze_text
import time

# ---------- KONFIGURASI HALAMAN & CSS ----------
st.set_page_config(page_title="Buzz & Framing Analyzer", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: white; border-radius: 12px; padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 1.5rem;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #28a745, #ffc107, #dc3545);
    }
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if 'df_raw' not in st.session_state:
    st.session_state.df_raw = None
if 'issues' not in st.session_state:
    st.session_state.issues = []
if 'current_issue_idx' not in st.session_state:
    st.session_state.current_issue_idx = None
if 'detail_analyzed' not in st.session_state:
    st.session_state.detail_analyzed = None
if 'compare_issues' not in st.session_state:
    st.session_state.compare_issues = []
if 'btn_clicked' not in st.session_state:
    st.session_state.btn_clicked = False

# ---------- FUNGSI ----------
@st.cache_data(show_spinner=False)
def fetch_data(keyword, max_news, max_tweets):
    news = scrape_google_news(keyword, max_articles=max_news)
    tweets = scrape_twitter(keyword, max_tweets=max_tweets)
    all_data = news + tweets
    df = pd.DataFrame(all_data)
    if 'text' in df.columns:
        df = df.dropna(subset=['text'])
        df = df.reset_index(drop=True)
    return df

def perform_clustering(df, keyword):
    texts_with_indices = [{'index': i, 'text': row['text']} for i, row in df.iterrows()]
    return cluster_issues(texts_with_indices, keyword)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Pengaturan")
    keyword = st.text_input("Masukkan isu / keyword", placeholder="contoh: Prabowo")
    col1, col2 = st.columns(2)
    with col1:
        max_news = st.slider("Berita", 0, 30, 10)
    with col2:
        max_tweets = st.slider("Tweet", 0, 50, 20)
    btn = st.button("Mulai Analisis", type="primary", use_container_width=True)

# Reset state jika keyword kosong
if not keyword:
    st.session_state.btn_clicked = False
    st.session_state.issues = []
    st.session_state.df_raw = None

# Proses tombol
if btn:
    st.session_state.btn_clicked = True
    st.session_state.issues = []   # reset isu lama
    st.session_state.df_raw = None

# ---------- WELCOME PAGE ----------
if not st.session_state.issues and not st.session_state.btn_clicked:
    st.title("🔍 Buzz & Framing Analyzer")
    st.markdown("## Selamat Datang! 👋")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🧠 Apa ini?")
        st.write("Alat cerdas untuk **membedah isu publik** secara otomatis.")
    with col2:
        st.markdown("### 🎯 Metode")
        st.write("Kumpulkan berita & cuitan, AI kelompokkan ke isu, nilai keorganikan & framing.")
    with col3:
        st.markdown("### 📖 Panduan Singkat")
        st.write("1. Masukkan keyword. 2. Atur jumlah. 3. Klik Mulai Analisis.")
    st.markdown("---")
    with st.expander("📌 Istilah: Organik vs Non-Organik"):
        st.write("Organik: konten alami. Non-Organik: ciri buzzer (pengulangan, polarisasi, dll).")
    with st.expander("🧩 Framing"):
        st.write("Sudut pandang: konflik, moralitas, ekonomi, dll.")
    st.stop()

# ---------- PROSES ANALISIS ----------
if st.session_state.btn_clicked and keyword:
    with st.spinner(f"🔎 Mencari berita dan tweet tentang '{keyword}'..."):
        df = fetch_data(keyword, max_news, max_tweets)
        if df.empty:
            st.warning("Tidak ditemukan data. Coba keyword lain.")
            st.session_state.btn_clicked = False
            st.stop()
        st.session_state.df_raw = df
        st.success(f"Terkumpul {len(df)} item ({len(df[df['platform']=='news'])} berita, {len(df[df['platform']=='twitter'])} tweet).")
        if len(df[df['platform']=='twitter']) == 0:
            st.info("ℹ️ Data Twitter tidak tersedia. Hanya berita yang ditampilkan.")
    
    with st.spinner("🧠 Mengelompokkan isu..."):
        issues = perform_clustering(df, keyword)
        st.session_state.issues = issues
        st.session_state.current_issue_idx = None
        st.session_state.detail_analyzed = None
        st.session_state.compare_issues = []
        st.session_state.btn_clicked = False
        st.success("Analisis isu selesai!")

# ---------- RINGKASAN ISU ----------
if st.session_state.issues:
    issues = st.session_state.issues
    st.title(f"📊 Ringkasan Isu Seputar '{keyword}'")
    cols = st.columns(min(3, len(issues)))
    for i, issue in enumerate(issues):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {issue.get('nama', 'Isu')}")
                st.caption(issue.get('deskripsi', ''))
                st.metric("Konten", issue.get('jumlah_konten', 0))
                non_org = issue.get('proporsi_non_organik', 0)
                st.progress(non_org / 100, text=f"Non-Organik: {non_org}%")
                framings = issue.get('framing_dominan', [])
                if framings:
                    st.markdown("**Framing:** " + ", ".join(f"`{f}`" for f in framings))
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔍 Detail", key=f"detail_{i}", use_container_width=True):
                        st.session_state.current_issue_idx = i
                        st.session_state.detail_analyzed = None
                        st.rerun()
                with col_btn2:
                    if st.button("➕ Bandingkan", key=f"comp_{i}", use_container_width=True):
                        if i not in st.session_state.compare_issues and len(st.session_state.compare_issues) < 2:
                            st.session_state.compare_issues.append(i)
                        else:
                            st.warning("Maksimal 2 isu.")
            st.divider()

    # ---------- BANDINGKAN ISU ----------
    if len(st.session_state.compare_issues) == 2:
        st.subheader("⚖️ Bandingkan Dua Isu")
        idx1, idx2 = st.session_state.compare_issues
        colA, colB = st.columns(2)
        with colA:
            st.markdown(f"**{issues[idx1].get('nama')}**")
            st.write(f"Konten: {issues[idx1].get('jumlah_konten')}")
            st.write(f"Non-Organik: {issues[idx1].get('proporsi_non_organik')}%")
        with colB:
            st.markdown(f"**{issues[idx2].get('nama')}**")
            st.write(f"Konten: {issues[idx2].get('jumlah_konten')}")
            st.write(f"Non-Organik: {issues[idx2].get('proporsi_non_organik')}%")
        if st.button("Hapus Perbandingan"):
            st.session_state.compare_issues = []
            st.rerun()

    # ---------- DETAIL ISU ----------
    if st.session_state.current_issue_idx is not None:
        idx = st.session_state.current_issue_idx
        st.subheader(f"🔎 Detail Isu: {issues[idx].get('nama')}")
        df_issue = st.session_state.df_raw.iloc[issues[idx].get('indeks_konten', [])]
        if not df_issue.empty:
            if st.session_state.detail_analyzed is None:
                with st.spinner("Menganalisis detail..."):
                    results = []
                    for _, row in df_issue.iterrows():
                        analysis = analyze_text(row['text'])
                        results.append({**row.to_dict(), **analysis})
                    st.session_state.detail_analyzed = pd.DataFrame(results)
            df_detail = st.session_state.detail_analyzed
            st.dataframe(df_detail[['source', 'username', 'text', 'buzzer_score', 'sentiment', 'framing', 'explanation']], width='stretch')
            avg_score = df_detail['buzzer_score'].mean()
            st.metric("Rata-rata Skor Non-Organik", f"{avg_score:.0f}/100")
        else:
            st.warning("Konten tidak tersedia.")

    # ---------- TANYA AI ----------
    st.subheader("💬 Tanya AI")
    user_q = st.chat_input("Tanyakan sesuatu tentang isu ini...")
    if user_q:
        all_text = " ".join(st.session_state.df_raw['text'].head(30))[:2500]
        prompt = f"Konteks: {all_text}\n\nPertanyaan: {user_q}\nJawab dalam bahasa Indonesia."
        from analyzer import get_client
        client = get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.5
        )
        st.chat_message("assistant").write(response.choices[0].message.content)
