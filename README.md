# avr-volume-overlay
This program shows an overlay on your PC when you adjust the volume on a Denon or Marantz AVR.
This is useful if you don't route video through your AVR via HDMI, which would offer similar functionality.

## Prerequisites
You need an Denon or Marantz AVR with telnet connectivity.
Only tested on Windows, but should work elsewhere.

Install dependencies:
```
pip install denonavr tkinter async_tkinter_loop
```

Set your AVR's IP address in the main function and run with `py.exe avr.py`
