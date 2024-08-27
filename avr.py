import denonavr
import sys
import time
import os
import tkinter as tk
import tkinter.font as tkFont
import asyncio
from async_tkinter_loop import async_mainloop, get_event_loop


AVR_IP_ADDRESS = '192.168.1.104'


class VolOverlay:
    def __init__(self):
        self.window = tk.Tk()
        self.vol_img = tk.PhotoImage(file='./icons/vol.png')
        self.mute_img = tk.PhotoImage(file='./icons/mute.png')
        self.vol_font = tkFont.Font(font=("Grandview Display", 20, tkFont.BOLD))
        self.format_font = tkFont.Font(font=("Consolas", 12))
        self.text = None
        self.img_label = None
        self.timer = None
        self.prev_vol = ''
        self.prev_muted = False
        self.last_audio_format = 'Unknown audio format'
        self._init_window()

    def _init_window(self):
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.80)
        self.window.configure(bg='#000000', padx=15, pady=5)
        self.img_label = tk.Label(self.window, image=self.vol_img, background="#000000", padx=15)
        self.img_label.pack(side="left")
        self.text = tk.Text(self.window, background="#000000", bd=0, highlightthickness=0, padx=15)
        self.text.tag_configure("volume", font=self.vol_font, foreground="#FFFFFF")
        self.text.tag_configure("format", font=self.format_font, foreground="#EEEEEE", lmargin1=2)
        self.text.pack(side="right", fill="both", expand=True)
        self.hide()

    def hide(self):
        self.window.withdraw()
        
    def show_vol(self, vol, muted):
        if self.timer is not None:
            self.timer.cancel()

        if vol is not None:
            self.prev_vol = vol
        if muted is not None:
            self.prev_muted = muted

        img = self.mute_img if muted else self.vol_img
        self.img_label.configure(image=img)
        self.text.delete("1.0", tk.END)
        self.text.delete("2.0", tk.END)
        self.text.insert("1.0", f'{self.prev_vol}\n', "volume")
        self.text.insert("2.0", f'{self.last_audio_format}\n', "format")
        self.adjust_window_width()
        self.window.deiconify()

        if not muted:
            overlay.timer = asyncio.create_task(self.hide_window())

    def adjust_window_width(self):
        screen_width = self.window.winfo_screenwidth()
        monospaced_text = self.text.get("2.0", "2.end")
        text_width_pixels = self.format_font.measure(monospaced_text)
        padding = 100
        new_width = text_width_pixels + padding
        margin = 25
        height = 65
        posx = screen_width - new_width - margin
        posy = margin
        self.window.geometry(f"{new_width}x{height}")
        self.window.geometry('%dx%d+%d+%d' % (new_width, height, posx, posy))

    def update_audio_format(self, format):
        self.last_audio_format = format

    async def hide_window(self, after=1):
        await asyncio.sleep(after)
        self.hide()


overlay = VolOverlay()


def convert_vol_to_string(value):
    if len(value) == 2:
        return str(float(value[0] + value[1] + ".0"))
    elif len(value) == 3 and value[2] == '5':
        return str(float(value[:2] + ".5"))
    else:
        raise ValueError("Invalid volume value")


async def update_callback(zone, event, parameter):
    muted = False
    vol = None
    if zone == "Main" and event == "MV" and parameter is not None:
        vol = convert_vol_to_string(parameter)
    elif zone == "Main" and event == "MU" and parameter is not None:
        muted = parameter == "ON"
    elif zone == "Main" and event == "MS" and parameter is not None:
        overlay.update_audio_format(parameter)
    else:
        print("Unhandled event: Zone: " + zone + " Event: " + event + " Parameter: " + parameter)
        return

    overlay.show_vol(vol, muted)


async def connect_avr(ip):
    print(f"Connecting to {ip}...")
    try:
        avr = denonavr.DenonAVR(ip)
        await avr.async_setup()
        await avr.async_telnet_connect()
        await avr.async_update()
        print("Ready!")
        return avr
    except denonavr.exceptions.AvrTimoutError:
        print(f"Failed to connect to {ip}, exiting.")
        sys.exit()


def main():
    if sys.platform.lower() == "win32" or os.name.lower() == "nt":
        from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    avr = get_event_loop().run_until_complete(connect_avr(AVR_IP_ADDRESS))
    avr.register_callback("ALL", update_callback)
    overlay.last_audio_format = avr.sound_mode_raw
    
    async_mainloop(overlay.window)


if __name__ == "__main__":
    main()
