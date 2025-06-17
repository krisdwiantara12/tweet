import tweepy
import os
import random
import requests
import tempfile
from bs4 import BeautifulSoup # Library baru untuk scraping

# --- KONFIGURASI ---
JUMLAH_TRENDING = 10 # Ambil 10 tren teratas

# Nama file-file Anda
CAPTIONS_FILE = "captions.txt"
LINKS_FILE = "links.txt"
GAMBAR_FILE = "gambar.txt"
# --------------------

def get_api_keys():
    """Mengambil semua kunci API dari GitHub Secrets."""
    keys = {
        "consumer_key": os.environ.get('TWITTER_API_KEY'),
        "consumer_secret": os.environ.get('TWITTER_API_SECRET'),
        "access_token": os.environ.get('TWITTER_ACCESS_TOKEN'),
        "access_token_secret": os.environ.get('TWITTER_ACCESS_SECRET')
    }
    if not all(keys.values()):
        print("❌ KESALAHAN: Kunci API Twitter tidak ditemukan.")
        return None
    return keys

def get_random_content(filename):
    """Membaca file teks dan memilih satu baris secara acak."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content_list = [line.strip() for line in f if line.strip()]
        if not content_list: return None
        return random.choice(content_list)
    except FileNotFoundError:
        print(f"❌ KESALAHAN: File '{filename}' tidak ditemukan.")
        return None

def download_image(image_url):
    """Mengunduh gambar dari URL dan menyimpannya ke file sementara."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(image_url, stream=True, headers=headers)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        for chunk in response.iter_content(1024):
            temp_file.write(chunk)
        
        temp_file.close()
        print(f"🖼️  Gambar berhasil diunduh ke: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        print(f"❌ GAGAL mengunduh gambar dari {image_url}: {e}")
        return None

def scrape_trending_topics():
    """
    Mengambil topik tren dengan scraping dari trends24.in.
    Ini adalah 'hack' untuk menggantikan API Twitter yang berbayar.
    """
    print("🔄 Mencoba mengambil topik trending dari trends24.in...")
    url = "https://trends24.in/indonesia/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Cari daftar tren. Tren ada di dalam <li> di dalam <ol class="trend-card__list">
        trend_list = soup.find('ol', class_='trend-card__list')
        
        if not trend_list:
            print("🟡 Gagal menemukan daftar tren di halaman. Mungkin struktur website berubah.")
            return ""
            
        trends = [item.get_text(strip=True) for item in trend_list.find_all('li')]
        
        if not trends:
            print("🟡 Tidak ada tren yang ditemukan di dalam daftar.")
            return ""

        # Ambil sejumlah tren yang ditentukan dari paling atas (paling kiri/baru)
        selected_trends = trends[:JUMLAH_TRENDING]
        print(f"✅ Tren berhasil diambil: {' '.join(selected_trends)}")
        return " ".join(selected_trends)
        
    except Exception as e:
        print(f"❌ GAGAL melakukan scraping tren: {e}")
        return "" # Kembalikan string kosong jika gagal, agar bot tidak berhenti

def main():
    """Fungsi utama untuk menjalankan bot."""
    print("🚀 Memulai proses tweet otomatis...")
    
    api_keys = get_api_keys()
    if not api_keys: return

    auth = tweepy.OAuth1UserHandler(api_keys["consumer_key"], api_keys["consumer_secret"], api_keys["access_token"], api_keys["access_token_secret"])
    api_v1 = tweepy.API(auth)
    client_v2 = tweepy.Client(consumer_key=api_keys["consumer_key"], consumer_secret=api_keys["consumer_secret"], access_token=api_keys["access_token"], access_token_secret=api_keys["access_token_secret"])

    # --- Kumpulkan Konten ---
    caption_template = get_random_content(CAPTIONS_FILE)
    link_to_insert = get_random_content(LINKS_FILE)
    image_url_to_upload = get_random_content(GAMBAR_FILE)
    trending_topics = scrape_trending_topics() # Panggil fungsi scraping baru
    
    if not caption_template:
        print("❌ Tidak ada template caption. Proses berhenti.")
        return

    # --- Gabungkan Teks Tweet ---
    final_caption = caption_template.replace('{Link}', link_to_insert or "")
    full_tweet_text = f"{final_caption}\n\n{trending_topics}".strip()

    # --- Proses dan Upload Gambar ---
    media_id = None
    temp_image_path = None
    if image_url_to_upload:
        temp_image_path = download_image(image_url_to_upload)
        if temp_image_path:
            try:
                media = api_v1.media_upload(filename=temp_image_path)
                media_id = media.media_id_string
                print(f"✅ Gambar berhasil diunggah ke Twitter. Media ID: {media_id}")
            except Exception as e:
                print(f"❌ GAGAL mengunggah gambar ke Twitter: {e}")
    
    # --- Kirim Tweet ---
    try:
        print(f"🕊️  Mencoba memposting tweet...")
        request_params = {"text": full_tweet_text}
        if media_id:
            request_params["media_ids"] = [media_id]
        
        response = client_v2.create_tweet(**request_params)
        print(f"✅ SUKSES! Tweet berhasil diposting. Tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"❌ GAGAL! Terjadi kesalahan saat memposting tweet: {e}")
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"🗑️  File sementara '{temp_image_path}' telah dihapus.")

if __name__ == "__main__":
    main()
