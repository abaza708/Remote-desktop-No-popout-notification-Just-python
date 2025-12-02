
# Abaza Remote Desktop

It contains almost all languages. It's the perfect starter for projects that can go in any direction.
## Features

- 🖥️ **Full HD Streaming** - 1920x1080 resolution at 40 FPS
- 🖱️ **Complete Control** - Mouse, keyboard, and scroll support
- 🔒 **Password Protected** - Secure authentication system
- 📊 **System Tray Integration** - Runs quietly in the background
- ⚡ **Optimized Performance** - JPEG compression and TCP optimization
- 🎯 **Pixel-Perfect Mouse** - Accurate coordinate mapping
- 🔔 **Silent Mode** - No popups, only terminal notifications

## Requirements

- Python 3.8 or higher
- Windows, Linux, or macOS

### Python Dependencies

```bash
pip install mss pillow pynput pystray
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install mss pillow pynput pystray
   ```
3. Run the server on the computer you want to control
4. Run the client on the computer you want to control from

## Usage

### Server (Computer to be controlled)

1. Run the server:
   ```bash
   python server_last.py
   ```

2. On first run, you'll see a setup dialog:
   - Read and accept the terms of service
   - Set a strong password (minimum 4 characters)
   - Click "I Accept & Start"

3. The server will start and display:
   ```
   🚀 Abaza Server Started Successfully!
   📍 Local IP: 192.168.1.100
   🔑 Port: 5555
   🔒 Password: yourpassword
   ⏳ Waiting for incoming connections...
   ```

4. Share your IP address and password with the person who needs to connect

5. The server runs in the system tray:
   - **Gray icon** = Waiting for connection
   - **Green icon** = Connected
   - Right-click icon for options

### Client (Controller)

1. Run the client:
   ```bash
   python control_last.py
   ```

2. Click the "📡 Connect" button

3. Enter connection details:
   - **Server IP**: The IP address from the server (e.g., 192.168.1.100)
   - **Port**: 5555 (default)
   - **Password**: The password set on the server

4. Click "🚀 Connect"

5. Once connected, you can:
   - Move mouse to control the remote computer
   - Click anywhere to interact
   - Type on your keyboard
   - Right-click for context menus
   - Scroll with mouse wheel

## Network Setup

### Local Network (Same WiFi/Ethernet)

Use the local IP address displayed by the server (e.g., 192.168.1.100)

### Internet (Remote Access)

1. **Port Forwarding**: Forward port 5555 on your router to the server's local IP
2. **Find Public IP**: Visit https://whatismyipaddress.com
3. **Connect**: Use the public IP address in the client

**Note**: Ensure your firewall allows connections on port 5555

## Security

- ✅ Password authentication required
- ✅ Visual indicator when connected (green tray icon)
- ✅ Manual disconnect option
- ✅ No automatic startup
- ⚠️ Use strong passwords (8+ characters recommended)
- ⚠️ Only share access with trusted individuals
- ⚠️ Disconnect when not in use

## Configuration

Edit these values in `server_last.py` to customize:

```python
self.port = 5555              # Change port number
self.jpeg_quality = 85        # Image quality (60-95)
self.stream_width = 1920      # Stream resolution width
self.stream_height = 1080     # Stream resolution height
```

## Performance Tips

- **Slow connection?** Reduce `jpeg_quality` to 70 or lower
- **Low bandwidth?** Reduce `stream_width` to 1600 and `stream_height` to 900
- **Laggy?** Check your network speed and close bandwidth-heavy applications
- **CPU usage?** Lower resolution or reduce frame rate

## Troubleshooting

### "Connection Refused"
- Make sure the server is running
- Check the IP address is correct
- Verify firewall settings
- Ensure port 5555 is not blocked

### "Authentication Failed"
- Double-check the password
- Passwords are case-sensitive
- Re-enter carefully

### Mouse Not Accurate
- The client window should match the aspect ratio
- Try running in fullscreen or maximized window
- Ensure the latest version is being used

### Poor Video Quality
- Increase `jpeg_quality` in server settings
- Check network bandwidth
- Reduce other network usage

### Server Won't Start
- Check if port 5555 is already in use
- Try running as administrator (Windows) or with sudo (Linux)
- Check Python version (3.8+ required)

## Technical Details

- **Protocol**: TCP/IP
- **Image Format**: JPEG compression
- **Resolution**: 1920x1080 (configurable)
- **Frame Rate**: ~40 FPS
- **Quality**: 85% JPEG (configurable)
- **Latency**: Optimized with TCP_NODELAY
- **Buffer Size**: 256KB send/receive buffers

## File Structure

```
├── server_last.py      # Server application (run on controlled PC)
├── control_last.py     # Client application (run on controller PC)
└── README.md           # This file
```

## System Tray Commands (Server)

Right-click the tray icon to:
- **Status** - View connection status and IP address
- **Disconnect** - End current remote session
- **Quit** - Stop server and exit

## Keyboard Shortcuts (Client)

All keyboard input is passed through to the remote computer:
- Standard keys (A-Z, 0-9, etc.)
- Modifiers (Ctrl, Alt, Shift)
- Special keys (Enter, Tab, Backspace, Delete, Esc)
- Arrow keys (Up, Down, Left, Right)

## License

This project is provided as-is for personal and educational use.

## Disclaimer

**USE AT YOUR OWN RISK**

- This software allows full control of your computer
- Only share access with trusted individuals
- Developers are not liable for any misuse or damages
- Always monitor the system tray icon when running

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all requirements are installed
3. Ensure network connectivity
4. Check firewall settings

---

