"""Diagnostic: test if GetAsyncKeyState can detect key presses.
Polls for 15 seconds, writes results to tests/hotkey_result.txt
"""
import ctypes
import time

user32 = ctypes.windll.user32

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_SPACE = 0x20

results = []
results.append(f"Started at {time.strftime('%H:%M:%S')}")
results.append("Polling keys for 15 seconds... press Ctrl+Shift+Space")

start = time.time()
detected_any = False
while time.time() - start < 15:
    ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
    shift = bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
    space = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)

    if ctrl or shift or space:
        msg = f"  t={time.time()-start:.2f}s ctrl={ctrl} shift={shift} space={space}"
        results.append(msg)
        if not detected_any:
            detected_any = True
    time.sleep(0.05)

if not detected_any:
    results.append("NO KEYS DETECTED - GetAsyncKeyState returned 0 for all keys")

results.append(f"Ended at {time.strftime('%H:%M:%S')}")

with open("tests/hotkey_result.txt", "w") as f:
    f.write("\n".join(results))

print("\n".join(results))
