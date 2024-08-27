# avr-volume-overlay
This program shows an overlay on your PC when you adjust the volume on a Denon or Marantz AVR.
This is useful if you don't route video through your AVR via HDMI, which would offer similar functionality.

## Prerequisites
You need an Denon or Marantz AVR with telnet connectivity.
Only tested on Windows, but should work elsewhere.

Install dependencies:
```
pip install denonavr async_tkinter_loop
```

## Usage
Set your AVR's IP address to the `AVR_IP_ADDRESS` variable in the `avr.py` and test with `py.exe avr.py`.

When everything works, you can for example in Windows use the Task Scheduler to run the script after user login. Use `pyw.exe` (or `pythonw.exe`) as the script to run to avoid command prompt appearing, and set the path to `avr.py` as an argument.

When adjusting volume, the overlay should appear in the top right corner of the screen, and disappear after one second.

![alt text](https://github.com/stuomas/avr-volume-overlay/blob/main/screenshot.jpg?raw=true)
