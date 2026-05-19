import os
import json
from groq import Groq

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets["GROQ_API_KEY"]
        except:
            raise ValueError("GROQ_API_KEY tidak ditemukan")
    return Groq(api_key=api_key)

def analyze_text(text):
    if not text or len(text.strip()) < 10:
        return None
    client = get_client()
    prompt = f"""
Anda adalah analis media sosial yang mendeteksi konten tidak organik (buzzer) dan framing.
Analisis teks berikut dan berikan output HANYA JSON.
JSON berisi:
- buzzer_score (0-100)
- indikator (list: pola_koordinasi, emosi_buatan, narasi_seragam, ajakan_terbuka, polarisasi, amplifikasi, anonimitas)
- framing (list: konflik, moralitas, ekonomi, human_interest, ketakutan, harapan, kepemimpinan, krisis, patriotisme, agama)
- sentiment (positif/negatif/netral)
- emotion (list: marah, takut, sedih, senang, terkejut, jijik, percaya, antisipasi)
- bias_words (list kata/frasa tendensius)
- explanation (2-3 kalimat penjelasan)

Teks: "{text[:1500]}"
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
        return json.loads(content)
    except Exception as e:
        return {"error": str(e), "buzzer_score": None, "framing": [], "bias_words": [], "sentiment": "error", "emotion": [], "explanation": f"Error: {e}"}

def cluster_issues(texts_with_indices, keyword):
    """
    Mengelompokkan teks (list of dict: {index, text}) menjadi isu.
    Mengembalikan list isu: [{nama, deskripsi, indeks_konten, framing_dominan, proporsi_non_organik, jumlah_konten}]
    """
    client = get_client()
    # Buat mapping indeks asli ke teks pendek
    items = []
    for item in texts_with_indices:
        # Potong teks untuk input prompt
        short_text = item['text'][:200].replace('\n', ' ')
        items.append(f"[{item['index']}] {short_text}")
    all_texts = "\n".join(items)

    prompt = f"""
Anda adalah analis isu. Di bawah ini adalah daftar teks dari berbagai sumber tentang "{keyword}".
Tugas Anda:
1. Kelompokkan teks-teks tersebut ke dalam beberapa isu/topik yang berbeda (maksimal 5 isu).
2. Beri nama singkat dan deskripsi singkat untuk setiap isu.
3. Tentukan framing dominan untuk isu tersebut (pilih dari: konflik, moralitas, ekonomi, human_interest, ketakutan, harapan, kepemimpinan, krisis, patriotisme, agama).
4. Perkirakan proporsi konten yang TIDAK ORGANIK (buzzer/terkoordinasi) di dalam isu tersebut dalam persen (0-100). Lihat dari ciri-ciri: bahasa provokatif, repetisi, polarisasi, tanpa opini personal.
5. Cantumkan indeks konten (dalam kurung siku) yang termasuk dalam isu tersebut.

Output HANYA JSON dengan struktur:
{{
  "isu": [
    {{
      "nama": "string",
      "deskripsi": "string",
      "indeks_konten": [0, 3, 5],
      "framing_dominan": ["string"],
      "proporsi_non_organik": 60,
      "jumlah_konten": 3
    }}
  ]
}}

Pastikan semua indeks konten terpakai dalam salah satu isu.

Daftar teks:
{all_texts}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
        result = json.loads(content)
        return result.get("isu", [])
    except Exception as e:
        print(f"Error clustering: {e}")
        # Fallback: semua konten jadi satu isu
        return [{
            "nama": f"Isu {keyword}",
            "deskripsi": "Semua konten terkait",
            "indeks_konten": [item['index'] for item in texts_with_indices],
            "framing_dominan": ["lainnya"],
            "proporsi_non_organik": 50,
            "jumlah_konten": len(texts_with_indices)
        }]