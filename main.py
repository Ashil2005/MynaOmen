import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError
import threading
import random
import time
import pyautogui
import keyboard
import os
import glob
from playsound import playsound
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Listener as KeyListener

# === Asset Paths ===
FLYING_SETS = [sorted(glob.glob(f"assets/flya{i}_*.png")) for i in range(1, 5)]
STANDING_SETS = [sorted(glob.glob(f"assets/standa{i}_*.png")) for i in range(1, 5)]
MYNA_SOUND_PATH = "assets/myna_call.wav"

# === Constants ===
BIRD_WIDTH, BIRD_HEIGHT = 360, 360
animation_speed_multiplier = 1.0
active_zones = []
curse_active = False
curse_indicator = None

main_root = tk.Tk()
main_root.withdraw()
mouse = MouseController()

# === Animation Helpers ===
def load_frames(file_list):
    frames = []
    for f in file_list:
        try:
            image = Image.open(f).convert("RGBA").resize((BIRD_WIDTH, BIRD_HEIGHT))
            frames.append(ImageTk.PhotoImage(image))
        except (UnidentifiedImageError, FileNotFoundError) as e:
            print(f"⚠️ Skipping invalid image: {f} ({e})")
    return frames

def animate_frames(label, frames, delay, control):
    def loop(i=0):
        if not control.get("running", True) or not label.winfo_exists():
            return
        label.configure(image=frames[i])
        label.image = frames[i]
        adjusted = int(delay * animation_speed_multiplier)
        control["job"] = label.after(adjusted, loop, (i + 1) % len(frames))
    loop()

def stop_animation(control, label):
    control["running"] = False
    if control.get("job") and label.winfo_exists():
        try:
            label.after_cancel(control["job"])
        except Exception as e:
            print(f"⚠️ Failed to cancel animation: {e}")

def play_sound(path):
    if not os.path.exists(path): return
    try:
        threading.Thread(target=playsound, args=(path,), daemon=True).start()
    except Exception as e:
        print(f"🎧 Sound error: {e}")

def fly_away(window, x, y):
    screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
    target_x, target_y = random.choice([(0, 0), (screen_w, 0), (0, screen_h), (screen_w, screen_h)])
    steps = 150
    dx, dy = (target_x - x) / steps, (target_y - y) / steps

    for _ in range(steps):
        x += dx
        y += dy
        if window.winfo_exists():
            window.geometry(f"{BIRD_WIDTH}x{BIRD_HEIGHT}+{int(x)}+{int(y)}")
            window.update()
        time.sleep(0.03 * animation_speed_multiplier)

    zone = (int(x) // 100, int(y) // 100)
    if zone in active_zones:
        active_zones.remove(zone)
    if window.winfo_exists():
        window.destroy()

# === Speed Controls ===
def apply_slowdown():
    global animation_speed_multiplier
    animation_speed_multiplier = 2.0
    print("🐢 Slowdown applied")

def apply_boost():
    global animation_speed_multiplier
    animation_speed_multiplier = 0.5
    print("⚡ Speed boost applied")
    threading.Thread(target=reset_speed_after, args=(6,), daemon=True).start()

def reset_speed_after(duration):
    global animation_speed_multiplier
    time.sleep(duration)
    animation_speed_multiplier = 1.0
    print("🔄 Speed reset")

# === Curse Indicator ===
def show_curse_indicator():
    global curse_indicator
    if curse_indicator: return

    curse_indicator = tk.Toplevel()
    curse_indicator.overrideredirect(True)
    curse_indicator.wm_attributes("-topmost", True)
    curse_indicator.configure(bg="black")
    label = tk.Label(curse_indicator, text="☠️ CURSED", fg="red", bg="black", font=("Arial", 14, "bold"))
    label.pack()
    update_curse_indicator_position()

def update_curse_indicator_position():
    if curse_indicator and curse_indicator.winfo_exists():
        screen_w = main_root.winfo_screenwidth()
        curse_indicator.geometry(f"+{int(screen_w / 2 - 70)}+20")
        curse_indicator.after(1000, update_curse_indicator_position)

def hide_curse_indicator():
    global curse_indicator
    if curse_indicator:
        try:
            curse_indicator.destroy()
        except:
            pass
        curse_indicator = None

# === Curse Effects ===
def cursed_cursor_drift():
    while True:
        if curse_active:
            try:
                x, y = mouse.position
                mouse.position = (x - random.randint(-15, 15), y - random.randint(-15, 15))
            except:
                pass
        time.sleep(0.3)

def cursed_keyboard_scramble():
    def on_press(key):
        if not curse_active:
            return
        try:
            if hasattr(key, 'char') and key.char and random.random() < 0.15:
                fake = random.choice("abcdefghijklmnopqrstuvwxyz1234567890")
                print(f"🧿 Replacing '{key.char}' with '{fake}'")
                keyboard.write(fake)
                return False
        except:
            pass

    while True:
        if curse_active:
            with KeyListener(on_press=on_press) as listener:
                while curse_active:
                    time.sleep(0.1)
                listener.stop()
        else:
            time.sleep(1)

# === Bird Logic ===
def show_myna():
    bird_window = tk.Toplevel()
    bird_window.overrideredirect(True)
    bird_window.wm_attributes("-topmost", True)
    bird_window.configure(bg="white")

    screen_w = bird_window.winfo_screenwidth()
    screen_h = bird_window.winfo_screenheight()

    for _ in range(10):
        landing_x = random.randint(100, screen_w - BIRD_WIDTH - 100)
        landing_y = random.randint(int(screen_h * 0.35), int(screen_h * 0.65))
        zone = (landing_x // 100, landing_y // 100)
        if zone not in active_zones:
            active_zones.append(zone)
            break
    else:
        bird_window.destroy()
        return

    entry_from = random.choice(["left", "right", "top"])
    start_x, start_y = {
        "left": (-BIRD_WIDTH, landing_y),
        "right": (screen_w + BIRD_WIDTH, landing_y),
        "top": (landing_x, -BIRD_HEIGHT)
    }[entry_from]

    label = tk.Label(bird_window, bg="white")
    label.pack()

    def bird_life():
        try:
            play_sound(MYNA_SOUND_PATH)

            fly_in_frames = load_frames(random.choice(FLYING_SETS))
            fly_in_ctrl = {"running": True}
            animate_frames(label, fly_in_frames, delay=90, control=fly_in_ctrl)

            steps = 150
            current_x, current_y = start_x, start_y
            dx, dy = (landing_x - start_x) / steps, (landing_y - start_y) / steps
            for _ in range(steps):
                current_x += dx
                current_y += dy
                if bird_window.winfo_exists():
                    bird_window.geometry(f"{BIRD_WIDTH}x{BIRD_HEIGHT}+{int(current_x)}+{int(current_y)}")
                    bird_window.update()
                time.sleep(0.025 * animation_speed_multiplier)

            stop_animation(fly_in_ctrl, label)
            time.sleep(0.3 * animation_speed_multiplier)

            standing_frames = load_frames(random.choice(STANDING_SETS))
            stand_ctrl = {"running": True}
            animate_frames(label, standing_frames, delay=120, control=stand_ctrl)

            time.sleep(random.randint(8, 12) * animation_speed_multiplier)
            stop_animation(stand_ctrl, label)

            fly_out_frames = load_frames(random.choice(FLYING_SETS))
            fly_out_ctrl = {"running": True}
            animate_frames(label, fly_out_frames, delay=85, control=fly_out_ctrl)

            time.sleep(0.8 * animation_speed_multiplier)
            fly_away(bird_window, landing_x, landing_y)

        except Exception as e:
            print(f"🐦 Error in bird_life: {e}")

    threading.Thread(target=bird_life, daemon=True).start()

# === Topmost Alert Fix ===
def force_alert(message, title="Notice"):
    def show():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        pyautogui.alert(message, title)
        root.destroy()

    threading.Thread(target=show).start()

# === Omen Logic ===
def trigger_omen():
    global curse_active
    num_birds = random.choice([1, 2])
    for _ in range(num_birds):
        main_root.after(0, show_myna)
    time.sleep(1)

    if num_birds == 1:
        force_alert("☠️ You are cursed by the lonely Myna!\n\n'One for sorrow...'", "Bad Omen")
        apply_slowdown()
        curse_active = True
        show_curse_indicator()
        force_alert("😱 Things might go wrong today!", "Bad Omen")
    else:
        force_alert("✨ You are blessed by the Myna duo!\n\n'Two for joy!'", "Good Omen")
        if curse_active:
            force_alert("💫 The curse has been lifted!", "Relief")
        curse_active = False
        hide_curse_indicator()
        apply_boost()
        force_alert("🌈 Everything feels lighter and joyful!", "Good Omen")

# === Startup Threads ===
def start_loop():
    while True:
        time.sleep(random.randint(20, 40))
        trigger_omen()

def quit_listener():
    print("🔴 Press CTRL + SHIFT + Q to quit anytime.")
    keyboard.wait("ctrl+shift+q")
    os._exit(0)

# === Launch App ===
if __name__ == "__main__":
    threading.Thread(target=start_loop, daemon=True).start()
    threading.Thread(target=quit_listener, daemon=True).start()
    threading.Thread(target=cursed_cursor_drift, daemon=True).start()
    threading.Thread(target=cursed_keyboard_scramble, daemon=True).start()
    main_root.mainloop()
