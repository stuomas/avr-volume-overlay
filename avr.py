import denonavr
import sys
import os
import tkinter as tk
import asyncio
from async_tkinter_loop import async_mainloop, get_event_loop


class VolOverlay:
    def __init__(self):
        self.window = tk.Tk()
        self.width = 200
        self.height = 60
        self.posx = 2560 - self.width - 25
        self.posy = 0 + 25
        self.vol_img = tk.PhotoImage(file='./icons/vol.png')
        self.mute_img = tk.PhotoImage(file='./icons/mute.png')
        self.label = None
        self.timer = None
        self.prev_vol = None
        self._init_window()

    def _init_window(self):
        self.window.geometry('%dx%d+%d+%d' % (self.width, self.height, self.posx, self.posy))
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.90)
        self.window.configure(bg='#000000')
        self.label = tk.Label(self.window)
        self.hide()

    def hide(self):
        self.window.withdraw()
        
    def show_vol(self, vol, muted):
        if vol:
            self.prev_vol = vol
        self.window.deiconify()
        img = self.mute_img if muted else self.vol_img
        self.label.config(
            text=f'{self.prev_vol}',
            font=("Source Sans Pro", 32),
            image=img, compound=tk.LEFT,
            bg='#000000',
            fg='#ffffff',
            padx=15,
        )
        self.label.pack(expand=True)

overlay = VolOverlay()


async def hide_window():
    await asyncio.sleep(1)
    overlay.hide()


def convert_vol_to_string(value):
    if len(value) == 2:
        return str(float(value[0] + value[1] + ".0"))
    elif len(value) == 3 and value[2] == '5':
        return str(float(value[:2] + ".5"))
    else:
        raise ValueError("Invalid volume value")


async def update_callback(zone, event, parameter):
    if overlay.timer is not None:
        overlay.timer.cancel()

    muted = False
    vol = None
    if zone == "Main" and event == "MV":
        vol = convert_vol_to_string(parameter)
    elif zone == "Main" and event == "MU":
        muted = parameter == "ON"
    else:
        print("Unhandled event: Zone: " + zone + " Event: " + event + " Parameter: " + parameter)
        return

    overlay.show_vol(vol, muted)

    if not muted:
        overlay.timer = asyncio.create_task(hide_window())


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

    denon_ip = '192.168.1.104'
    avr = get_event_loop().run_until_complete(connect_avr(denon_ip))
    avr.register_callback("ALL", update_callback)
    
    async_mainloop(overlay.window)


if __name__ == "__main__":
    main()
