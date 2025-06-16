import tweepy
import os
import random

# --- KONFIGURASI ---
# ID Lokasi untuk Tren Twitter. 1020075 adalah ID untuk Indonesia.
WOEID_INDONESIA = 1020075

# Jumlah kata & hashtag trending yang ingin diambil.
# PERINGATAN: Menggunakan angka tinggi (seperti 10) sangat berisiko tinggi
# dan dapat menyebabkan akun Anda ditangguhkan dengan cepat.
JUMLAH_TRENDING = 10

# Nama file dan folder
CAPTIONS_FILE = "captions.txt" # File ini sekarang berisi template tweet
LINKS_FILE = "links.txt"       # File ini berisi link untuk menggantikan placeholder {Link}
IMAGES_FOLDER = "images"       # Nama folder untuk menyimpan gambar Anda
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
        print("❌ KESALAHAN: Kunci API Twitter tidak ditemukan. Pastikan sudah diatur di GitHub Secrets.")
        return None
    return keys

def get_random_content(filename):
    """Membaca file teks dan memilih satu baris secara acak."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content_list = [line.strip() for line in f if line.strip()]
        if not content_list:
            print(f"⚠️ PERINGATAN: File '{filename}' kosong.")
            return None
        return random.choice(content_list)
    except FileNotFoundError:
        print(f"❌ KESALAHAN: File '{filename}' tidak ditemukan.")
        return None

def get_random_image(folder):
    """Memilih path gambar acak dari folder yang ditentukan."""
    try:
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if not files:
            return None # Tidak mencetak peringatan jika tidak ada gambar (opsional)
        return os.path.join(folder, random.choice(files))
    except FileNotFoundError:
        return None # Tidak mencetak kesalahan jika folder tidak ada (opsional)

def get_trending_topics(api):
    """Mengambil kata DAN hashtag yang sedang tren dari Twitter Indonesia."""
    print("🔄 Mengambil topik trending dari Twitter...")
    try:
        trends = api.get_place_trends(id=WOEID_INDONESIA)
        # Ambil nama tren (sekarang termasuk hashtag)
        trending_items = [trend['name'] for trend in trends[0]['trends']]
        if not trending_items:
            print("⚠️ PERINGATAN: Tidak bisa menemukan topik trending.")
            return ""
        
        # Ambil beberapa item secara acak dan gabungkan
        selected_trends = random.sample(trending_items, min(len(trending_items), JUMLAH_TRENDING))
        return " ".join(selected_trends)
    except Exception as e:
        print(f"❌ GAGAL mengambil tren: {e}")
        return ""

def main():
    """Fungsi utama untuk menjalankan bot."""
    print("🚀 Memulai proses tweet otomatis...")
    
    api_keys = get_api_keys()
    if not api_keys: return

    # --- Inisialisasi API ---
    auth = tweepy.OAuth1UserHandler(api_keys["consumer_key"], api_keys["consumer_secret"], api_keys["access_token"], api_keys["access_token_secret"])
    api_v1 = tweepy.API(auth)
    client_v2 = tweepy.Client(consumer_key=api_keys["consumer_key"], consumer_secret=api_keys["consumer_secret"], access_token=api_keys["access_token"], access_token_secret=api_keys["access_token_secret"])

    # --- Kumpulkan Konten ---
    caption_template = get_random_content(CAPTIONS_FILE)
    link_to_insert = get_random_content(LINKS_FILE)
    image_path = get_random_image(IMAGES_FOLDER)
    trending_topics = get_trending_topics(api_v1)
    
    if not caption_template:
        print("❌ Tidak ada template caption di captions.txt. Proses berhenti.")
        return

    # --- Buat Teks Tweet dari Template ---
    # Gantikan placeholder {Link} dengan link sebenarnya
    if link_to_insert:
        final_caption = caption_template.replace('{Link}', link_to_insert)
    else:
        # Jika tidak ada link, hapus placeholder dari template
        final_caption = caption_template.replace('{Link}', '')

    # Gabungkan caption dengan trending topics
    full_tweet_text = f"{final_caption}\n\n{trending_topics}".strip()

    # --- Proses Gambar ---
    media_id = None
    if image_path:
        print(f"🖼️  Mengunggah gambar: {image_path}")
        try:
            media = api_v1.media_upload(filename=image_path)
            media_id = media.media_id_string
            print(f"✅ Gambar berhasil diunggah. Media ID: {media_id}")
        except Exception as e:
            print(f"❌ GAGAL mengunggah gambar: {e}")

    print(f"\n📜 Teks Tweet yang akan diposting:\n--------------------------------\n{full_tweet_text}\n--------------------------------")

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

if __name__ == "__main__":
    main()
