import tweepy
import os
import random
import requests # Library baru untuk mengunduh gambar
import tempfile # Library untuk membuat file sementara

# --- KONFIGURASI ---
WOEID_INDONESIA = 1020075
JUMLAH_TRENDING = 10

# Nama file-file Anda
CAPTIONS_FILE = "captions.txt"
LINKS_FILE = "links.txt"
GAMBAR_FILE = "gambar.txt" # File baru untuk daftar URL gambar Anda
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

def get_trending_topics(api):
    """Mengambil topik tren dari Twitter."""
    print("🔄 Mengambil topik trending...")
    try:
        trends = api.get_place_trends(id=WOEID_INDONESIA)
        trending_items = [trend['name'] for trend in trends[0]['trends']]
        if not trending_items: return ""
        selected_trends = random.sample(trending_items, min(len(trending_items), JUMLAH_TRENDING))
        return " ".join(selected_trends)
    except Exception as e:
        print(f"❌ GAGAL mengambil tren: {e}")
        return ""

def download_image(image_url):
    """Mengunduh gambar dari URL dan menyimpannya ke file sementara."""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status() # Cek jika ada error http
        
        # Membuat file sementara untuk menyimpan gambar
        # 'delete=False' agar kita bisa menggunakan path-nya
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        for chunk in response.iter_content(1024):
            temp_file.write(chunk)
        
        temp_file.close()
        print(f"🖼️  Gambar berhasil diunduh ke: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        print(f"❌ GAGAL mengunduh gambar dari {image_url}: {e}")
        return None

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
    image_url_to_upload = get_random_content(GAMBAR_FILE) # Ambil URL gambar
    trending_topics = get_trending_topics(api_v1)
    
    if not caption_template:
        print("❌ Tidak ada template caption. Proses berhenti.")
        return

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
        print("🕊️  Mencoba memposting tweet...")
        request_params = {"text": full_tweet_text}
        if media_id:
            request_params["media_ids"] = [media_id]
        
        response = client_v2.create_tweet(**request_params)
        print(f"✅ SUKSES! Tweet berhasil diposting. Tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"❌ GAGAL! Terjadi kesalahan saat memposting tweet: {e}")
    finally:
        # Selalu hapus file gambar sementara setelah selesai
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"🗑️  File sementara '{temp_image_path}' telah dihapus.")

if __name__ == "__main__":
    main()
