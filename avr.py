import denonavr
import sys
import time
import os
import tkinter as tk
import tkinter.font as tkFont
import asyncio
from async_tkinter_loop import async_mainloop, get_event_loop


AVR_IP_ADDRESS = '192.168.1.104'
VOLUME_SCALE = 'absolute'


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
        self.last_audio_format = ''
        self.volume_scale = 'absolute'
        self._init_window()

    def _init_window(self):
        self.window.withdraw()
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

    def hide(self):
        self.window.withdraw()
        
    def show_vol(self, vol, muted):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

        if vol is not None:
            self.prev_vol = vol
        if muted is not None:
            self.prev_muted = muted
        if not self.prev_vol:
            return

        img = self.mute_img if self.prev_muted else self.vol_img
        self.img_label.configure(image=img)
        self.text.delete("1.0", tk.END)
        self.text.delete("2.0", tk.END)
        self.text.insert("1.0", f'{self.prev_vol}\n', "volume")
        if self.last_audio_format:
            self.text.insert("2.0", f'{self.last_audio_format}\n', "format")
        self.adjust_window_width()
        self.window.deiconify()

        if not self.prev_muted:
            try:
                loop = get_event_loop()
                self.timer = loop.create_task(self.hide_window())
            except RuntimeError:
                pass

    def adjust_window_width(self):
        screen_width = self.window.winfo_screenwidth()
        volume_text = self.text.get("1.0", "1.end")
        format_text = self.text.get("2.0", "2.end")
        volume_width = self.vol_font.measure(volume_text)
        format_width = self.format_font.measure(format_text)
        text_width_pixels = max(volume_width, format_width)
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

    def set_volume_scale(self, scale):
        self.volume_scale = scale

    async def hide_window(self, after=1):
        await asyncio.sleep(after)
        self.hide()


overlay = VolOverlay()


def format_volume(volume_db, volume_scale):
    if volume_scale == 'absolute':
        return f"{volume_db:+.1f} dB"
    else:
        relative_vol = volume_db + 80.0
        return f"{relative_vol:.1f}"


def convert_vol_to_string(value):
    if len(value) == 2:
        vol_db = float(value[0] + value[1]) - 80.0
    elif len(value) == 3 and value[2] == '5':
        vol_db = float(value[:2]) + 0.5 - 80.0
    else:
        raise ValueError("Invalid volume value")

    return vol_db


def update_callback(zone, event, parameter):
    muted = None
    vol_db = None
    if zone == "Main" and event == "MV" and parameter is not None:
        vol_db = convert_vol_to_string(parameter)
    elif zone == "Main" and event == "MU" and parameter is not None:
        muted = parameter == "ON"
    elif zone == "Main" and event == "MS" and parameter is not None:
        if parameter.lower() != "quick0":
            overlay.update_audio_format(parameter)
            if overlay.prev_muted and overlay.prev_vol:
                overlay.show_vol(None, None)
        return
    else:
        print("Unhandled event: Zone: " + zone + " Event: " + event + " Parameter: " + parameter)
        return

    if vol_db is not None:
        vol_str = format_volume(vol_db, overlay.volume_scale)
        overlay.show_vol(vol_str, muted)
    elif muted is not None:
        overlay.show_vol(None, muted)


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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    avr = loop.run_until_complete(connect_avr(AVR_IP_ADDRESS))
    overlay.set_volume_scale(VOLUME_SCALE)
    avr.register_callback("ALL", update_callback)
    
    async_mainloop(overlay.window, loop)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)
