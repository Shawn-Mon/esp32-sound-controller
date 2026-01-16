import socket
import pygame
import requests
import os
import sys

# ===== PATH FIX FOR EXE =====
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOUND_DIR = os.path.join(BASE_DIR, "sounds")

# ===== CONFIG =====
HOST = "0.0.0.0"
PORT = 5050
GITHUB_API = "https://api.github.com/repos/Shawn-Mon/esp32-sound-controller/contents/sounds"
# ==================

pygame.mixer.init()
os.makedirs(SOUND_DIR, exist_ok=True)

def sync_sounds():
    response = requests.get(GITHUB_API).json()
    sound_list = []

    for f in response:
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

# ===== TCP SERVER =====
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Waiting for ESP32...")
conn, addr = server.accept()
print("ESP32 connected:", addr)

conn.sendall(f"SHOW:{sounds[index]}\n".encode())

while True:
    data = conn.recv(1024).decode().strip()
    if not data:
        continue

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

    conn.sendall(f"SHOW:{sounds[index]}\n".encode())
