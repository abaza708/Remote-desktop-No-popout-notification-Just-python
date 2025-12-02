import socket
import threading
import mss
import pickle
import struct
import time
import tkinter as tk
from tkinter import messagebox
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import pystray
from PIL import Image, ImageDraw
import os
import sys
import io

class AbazaServer:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 5555
        self.password = None
        self.server_socket = None
        self.client_socket = None
        self.connected = False
        self.running = True
        self.tray_icon = None
        self.mouse_controller = MouseController()
        self.keyboard_controller = KeyboardController()
        self.jpeg_quality = 85
        self.stream_width = 1920
        self.stream_height = 1080
        
    def create_tray_icon(self):
        width = 64
        height = 64
        color1 = (70, 70, 70)  # Dark gray for disconnected
        color2 = (0, 200, 0)   # Green for connected
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        
        if self.connected:
            dc.rectangle([16, 16, 48, 48], fill=color2)
            dc.ellipse([18, 18, 46, 46], fill=(255, 255, 255))
            dc.text((24, 26), "ON", fill="black", font=None)
        else:
            dc.ellipse([16, 16, 48, 48], fill=(100, 100, 100))
            dc.text((20, 26), "OFF", fill="white", font=None)
        
        return image

    def update_tray_icon(self):
        if self.tray_icon:
            self.tray_icon.icon = self.create_tray_icon()
            title = f"Abaza - Connected (Port: {self.port})" if self.connected else f"Abaza - Waiting (Port: {self.port})"
            self.tray_icon.title = title

    def on_quit(self, icon, item):
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        icon.stop()
        os._exit(0)

    def on_disconnect(self, icon, item):
        if self.connected and self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            self.connected = False
            self.update_tray_icon()
            messagebox.showinfo("Abaza", "Remote connection disconnected")

    def show_status(self, icon, item):
        status = "CONNECTED" if self.connected else "WAITING FOR CONNECTION"
        messagebox.showinfo("Abaza Status", 
                          f"Status: {status}\n"
                          f"Port: {self.port}\n"
                          f"IP: {self.get_local_ip()}")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unknown"

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Status", self.show_status),
            pystray.MenuItem("Disconnect", self.on_disconnect, enabled=lambda item: self.connected),
            pystray.MenuItem("Quit", self.on_quit)
        )
        
        self.tray_icon = pystray.Icon(
            "Abaza",
            self.create_tray_icon(),
            f"Abaza - Waiting (Port: {self.port})",
            menu
        )
        
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_terms_and_setup(self):
        root = tk.Tk()
        root.title("Abaza Remote Desktop - Setup")
        root.geometry("650x500")
        root.resizable(False, False)
        
        terms_accepted = [False]
        password_var = tk.StringVar()
        
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = tk.Label(frame, text="Abaza Remote Desktop", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        terms_label = tk.Label(frame, text="Terms of Service", font=("Arial", 12, "bold"))
        terms_label.pack(pady=5)
        
        terms_text = tk.Text(frame, height=12, width=70, wrap=tk.WORD, font=("Arial", 9))
        terms_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(terms_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        terms_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=terms_text.yview)
        
        terms_content = """IMPORTANT - PLEASE READ CAREFULLY:

This software allows remote control of your computer. By using Abaza Remote Desktop, you agree that:

• Remote users can view your screen and control your mouse/keyboard when connected
• You will see visual indicators when someone is connected
• You can disconnect remote sessions at any time via system tray
• You are responsible for keeping your password secure
• Use at your own risk - the developers are not liable for any issues

SECURITY TIPS:
• Use a strong password
• Only share with trusted individuals
• Disconnect when not in use
• Monitor the system tray icon (Green = Connected)

Click 'I Accept' to continue, or 'Decline' to exit."""
        
        terms_text.insert("1.0", terms_content)
        terms_text.config(state=tk.DISABLED)
        
        password_frame = tk.Frame(frame)
        password_frame.pack(pady=10)
        
        pw_label = tk.Label(password_frame, text="Set Connection Password:", font=("Arial", 10))
        pw_label.pack(side=tk.LEFT, padx=5)
        
        pw_entry = tk.Entry(password_frame, textvariable=password_var, show="*", width=20, font=("Arial", 10))
        pw_entry.pack(side=tk.LEFT, padx=5)
        
        def on_accept():
            if not password_var.get().strip():
                messagebox.showerror("Error", "Please set a password")
                return
            if len(password_var.get()) < 4:
                messagebox.showerror("Error", "Password must be at least 4 characters")
                return
            terms_accepted[0] = True
            self.password = password_var.get().strip()
            root.destroy()
        
        def on_decline():
            root.destroy()
            sys.exit(0)
        
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)
        
        accept_btn = tk.Button(button_frame, text="I Accept & Start", command=on_accept, 
                               bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), 
                               width=15, height=1)
        accept_btn.pack(side=tk.LEFT, padx=10)
        
        decline_btn = tk.Button(button_frame, text="Decline & Exit", command=on_decline,
                               bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                               width=15, height=1)
        decline_btn.pack(side=tk.LEFT, padx=10)
        
        # Set focus and bind Enter key
        pw_entry.focus_set()
        root.bind('<Return>', lambda e: on_accept())
        
        root.protocol("WM_DELETE_WINDOW", on_decline)
        root.mainloop()
        
        return terms_accepted[0]

    def handle_client_commands(self):
        try:
            while self.connected and self.running:
                try:
                    # Receive command size
                    size_data = self.client_socket.recv(4)
                    if len(size_data) < 4:
                        break
                    data_size = struct.unpack("!I", size_data)[0]
                    
                    # Receive command data
                    data = b""
                    while len(data) < data_size:
                        chunk = self.client_socket.recv(min(65536, data_size - len(data)))
                        if not chunk:
                            break
                        data += chunk
                    
                    if not data:
                        break
                    
                    command = pickle.loads(data)
                    
                    # Execute command
                    if command['type'] == 'mouse_move':
                        # Get actual screen size for accurate scaling
                        with mss.mss() as sct:
                            monitor = sct.monitors[1]
                            screen_width = monitor['width']
                            screen_height = monitor['height']
                        
                        # Scale coordinates from image space to actual screen size
                        # Client sends coordinates in image space (1024x576)
                        scale_x = screen_width / command['client_width']
                        scale_y = screen_height / command['client_height']
                        
                        x = int(command['x'] * scale_x)
                        y = int(command['y'] * scale_y)
                        
                        # Clamp to screen bounds
                        x = max(0, min(screen_width - 1, x))
                        y = max(0, min(screen_height - 1, y))
                        
                        self.mouse_controller.position = (x, y)
                        
                    elif command['type'] == 'mouse_click':
                        button = Button.left if command['button'] == 'left' else Button.right
                        if command['pressed']:
                            self.mouse_controller.press(button)
                        else:
                            self.mouse_controller.release(button)
                            
                    elif command['type'] == 'mouse_scroll':
                        self.mouse_controller.scroll(command['dx'], command['dy'])
                        
                    elif command['type'] == 'key':
                        try:
                            key = command['key']
                            if command['pressed']:
                                if hasattr(Key, key):
                                    self.keyboard_controller.press(getattr(Key, key))
                                else:
                                    self.keyboard_controller.press(key)
                            else:
                                if hasattr(Key, key):
                                    self.keyboard_controller.release(getattr(Key, key))
                                else:
                                    self.keyboard_controller.release(key)
                        except Exception as e:
                            print(f"Key error: {e}")
                            
                    elif command['type'] == 'disconnect':
                        break
                        
                except Exception as e:
                    print(f"Command error: {e}")
                    break
                    
        except Exception as e:
            print(f"Command handler error: {e}")
        finally:
            self.connected = False
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
            self.client_socket = None
            self.update_tray_icon()

    def capture_and_send_screen(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            frame_time = 0.025
            
            while self.connected and self.running:
                try:
                    start_time = time.time()
                    
                    # Capture screen
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                    
                    # Resize for performance using faster algorithm
                    img = img.resize((self.stream_width, self.stream_height), Image.Resampling.BILINEAR)
                    
                    # Convert to JPEG for better compression
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=self.jpeg_quality, optimize=False)
                    data = buffer.getvalue()
                    
                    size = struct.pack("!I", len(data))
                    
                    # Send data
                    self.client_socket.sendall(size + data)
                    
                    # Adaptive frame rate
                    elapsed = time.time() - start_time
                    sleep_time = max(0, frame_time - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                except Exception as e:
                    print(f"Screen capture error: {e}")
                    break

    def start_server(self):
        config_file = os.path.join(os.path.expanduser("~"), ".abaza_config")
        
        if not os.path.exists(config_file):
            if not self.show_terms_and_setup():
                print("Setup declined by user.")
                return
            with open(config_file, 'w') as f:
                f.write(self.password)
            print("First-time setup completed.")
        else:
            with open(config_file, 'r') as f:
                self.password = f.read().strip()
            print("Loaded existing configuration.")
        
        self.setup_tray()
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            local_ip = self.get_local_ip()
            print(f"🚀 Abaza Server Started Successfully!")
            print(f"📍 Local IP: {local_ip}")
            print(f"🔑 Port: {self.port}")
            print(f"🔒 Password: {self.password}")
            print("⏳ Waiting for incoming connections...")
            print("-" * 50)
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client, addr = self.server_socket.accept()
                    
                    print(f"📡 Connection attempt from {addr[0]}:{addr[1]}")
                    
                    # Authenticate
                    auth_data = client.recv(1024).decode().strip()
                    if auth_data != self.password:
                        print("❌ Authentication failed: Invalid password")
                        client.close()
                        continue
                    
                    client.send(b"OK")
                    print("✅ Authentication successful!")
                    
                    # Enable TCP_NODELAY for lower latency
                    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    # Increase buffer sizes
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
                    
                    self.client_socket = client
                    self.connected = True
                    self.update_tray_icon()
                    
                    print(f"✅ Remote connection established from {addr[0]}")
                    print(f"📺 Streaming at {self.stream_width}x{self.stream_height}")
                    print("-" * 50)
                    
                    # Start service threads
                    screen_thread = threading.Thread(target=self.capture_and_send_screen, daemon=True)
                    command_thread = threading.Thread(target=self.handle_client_commands, daemon=True)
                    
                    screen_thread.start()
                    command_thread.start()
                    
                    # Wait for threads to complete
                    screen_thread.join()
                    command_thread.join()
                    
                    print("🔌 Connection closed")
                    self.connected = False
                    self.update_tray_icon()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if "accepted" in str(e):
                        continue
                    print(f"Connection error: {e}")
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            print("Server stopped.")

if __name__ == "__main__":
    server = AbazaServer()
    server.start_server()