import os
import time
import threading
import firebase_admin
from firebase_admin import credentials, firestore
import yt_dlp
from flask import Flask

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Media Processor is Live!", 200

# Firebase setup
# নিশ্চিত করুন key.json ফাইলটি আপলোড করা আছে
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def process_link(doc):
    data = doc.to_dict()
    url = data.get('url')
    print(f"Analyzing: {url}")
    
    ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            
            # Firestore ডাটাবেস আপডেট করা
            db.collection('downloads').document(doc.id).update({
                'download_url_hd': video_url,
                'status': 'completed'
            })
            print("Successfully processed!")
        except Exception as e:
            print(f"Error: {e}")

def firestore_listener():
    # Firestore-এ নতুন ডাটা এলে এটি নিজে থেকেই চালু হবে
    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED' or change.type.name == 'MODIFIED':
                doc = change.document
                if doc.to_dict().get('status') == 'pending':
                    process_link(doc)

    col_query = db.collection('downloads').where('status', '==', 'pending')
    col_query.on_snapshot(on_snapshot)
    while True: time.sleep(1)

# ব্যাকগ্রাউন্ড প্রসেস চালু করা
threading.Thread(target=firestore_listener, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

