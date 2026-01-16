import pygame
import requests
import os
import sys
import bluetooth

# ===== PATH FIX FOR EXE =====
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOUND_DIR = os.path.join(BASE_DIR, "sounds")
GITHUB_API = "https://api.github.com/repos/Shawn-Mon/esp32-sound-controller/contents/sounds"

pygame.mixer.init()
os.makedirs(SOUND_DIR, exist_ok=True)

def sync_sounds():
    files = requests.get(GITHUB_API).json()
    sound_list = []
    for f in files:
        if f["name"].endswith((".mp3", ".wav")):
            sound_list.append(f["name"])
            path = os.path.join(SOUND_DIR, f["name"])
            if not os.path.exists(path):
                data = requests.get(f["download_url"]).content
                with open(path, "wb") as file:
                    file.write(data)
    return sound_list

sounds = sync_sounds()
index = 0
paused = False

def play():
    pygame.mixer.music.load(os.path.join(SOUND_DIR, sounds[index]))
    pygame.mixer.music.play()

# ===== BLUETOOTH CONNECT =====
target_name = "ESP32_Sound"
target_address = None

nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
for addr, name in nearby_devices:
    if name == target_name:
        target_address = addr
        break

if target_address is None:
    print("ESP32 not found")
    exit(1)

print("Connecting to ESP32:", target_address)
port = 1
sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
sock.connect((target_address, port))

sock.send(f"SHOW:{sounds[index]}\n")

# ===== MAIN LOOP =====
while True:
    data = sock.recv(1024).decode().strip()
    if not data:
        continue

    # process commands from ESP32 (if needed)
    if data == "UP":
        index = (index - 1) % len(sounds)
    elif data == "DOWN":
        index = (index + 1) % len(sounds)
    elif data == "PLAY":
        if pygame.mixer.music.get_busy() and not paused:
            pygame.mixer.music.pause()
            paused = True
        elif paused:
            pygame.mixer.music.unpause()
            paused = False
        else:
            play()

    sock.send(f"SHOW:{sounds[index]}\n")
