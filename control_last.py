import socket
import pickle
import struct
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import time
import io

class AbazaClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.running = True
        self.current_image = None
        
        # Mouse optimization
        self.last_mouse_time = 0
        self.mouse_move_delay = 0.01
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.pending_mouse_event = None
        self.mouse_send_thread = None
        
        self.root = tk.Tk()
        self.root.title("Abaza Remote Desktop - Controller")
        self.root.geometry("1920x1080")
        self.root.configure(bg='black')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top control panel
        top_frame = tk.Frame(self.root, bg="#2c3e50", height=40)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.pack_propagate(False)
        
        # Title and status
        tk.Label(top_frame, text="Abaza Remote Desktop", 
                bg="#2c3e50", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(top_frame, text="● DISCONNECTED", 
                                    bg="#2c3e50", fg="#e74c3c", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Connection info
        self.info_label = tk.Label(top_frame, text="Not connected", 
                                  bg="#2c3e50", fg="#bdc3c7", font=("Arial", 9))
        self.info_label.pack(side=tk.LEFT, padx=10)
        
        # Buttons
        button_frame = tk.Frame(top_frame, bg="#2c3e50")
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        self.connect_btn = tk.Button(button_frame, text="📡 Connect", command=self.show_connect_dialog,
                                    bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                                    width=12, relief="flat")
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = tk.Button(button_frame, text="❌ Disconnect", command=self.disconnect,
                                       bg="#e74c3c", fg="white", font=("Arial", 9, "bold"),
                                       width=12, relief="flat", state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Screen display area
        self.screen_frame = tk.Frame(self.root, bg="black")
        self.screen_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.screen_frame, bg="black", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Store image reference
        self.photo_image = None
        self.image_id = None
        
        # Bind mouse events to canvas
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        
        # Bind keyboard events
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.focus_set()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Instructions
        help_text = "💡 Tip: Click on the screen to focus, then use mouse and keyboard to control remote computer"
        help_label = tk.Label(self.root, text=help_text, bg="#34495e", fg="#ecf0f1", 
                             font=("Arial", 8), pady=3)
        help_label.pack(fill=tk.X, side=tk.BOTTOM)

    def show_connect_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Connect to Remote Computer")
        dialog.geometry("400x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg='#ecf0f1')
        
        frame = tk.Frame(dialog, padx=25, pady=25, bg='#ecf0f1')
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Remote Connection Settings", 
                bg='#ecf0f1', fg="#2c3e50", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Server IP
        tk.Label(frame, text="Server IP Address:", bg='#ecf0f1', fg="#2c3e50", 
                font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        host_entry = tk.Entry(frame, width=20, font=("Arial", 10))
        host_entry.grid(row=1, column=1, pady=8, padx=10, sticky=tk.EW)
        host_entry.insert(0, "localhost")
        
        # Port
        tk.Label(frame, text="Port:", bg='#ecf0f1', fg="#2c3e50", 
                font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        port_entry = tk.Entry(frame, width=20, font=("Arial", 10))
        port_entry.grid(row=2, column=1, pady=8, padx=10, sticky=tk.EW)
        port_entry.insert(0, "5555")
        
        # Password
        tk.Label(frame, text="Password:", bg='#ecf0f1', fg="#2c3e50", 
                font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        password_entry = tk.Entry(frame, width=20, show="*", font=("Arial", 10))
        password_entry.grid(row=3, column=1, pady=8, padx=10, sticky=tk.EW)
        
        # Example IP
        example_frame = tk.Frame(frame, bg='#ecf0f1')
        example_frame.grid(row=4, column=0, columnspan=2, pady=10)
        tk.Label(example_frame, text="Example IPs: 192.168.1.100, 10.0.0.5, localhost", 
                bg='#ecf0f1', fg="#7f8c8d", font=("Arial", 8)).pack()
        
        def do_connect():
            host = host_entry.get().strip()
            if not host:
                messagebox.showerror("Error", "Please enter server IP address")
                return
                
            try:
                port = int(port_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid port number")
                return
                
            password = password_entry.get()
            if not password:
                messagebox.showerror("Error", "Please enter password")
                return
                
            dialog.destroy()
            self.connect(host, port, password)
        
        button_frame = tk.Frame(frame, bg='#ecf0f1')
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="🚀 Connect", command=do_connect,
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), 
                 width=12, height=1, relief="flat").pack(side=tk.LEFT, padx=10)
                 
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#95a5a6", fg="white", font=("Arial", 10, "bold"),
                 width=10, height=1, relief="flat").pack(side=tk.LEFT, padx=10)
        
        # Set focus and bind Enter key
        host_entry.focus_set()
        host_entry.select_range(0, tk.END)
        dialog.bind('<Return>', lambda event: do_connect())
        
        # Make entry fields expand
        frame.columnconfigure(1, weight=1)

    def connect(self, host, port, password):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(8.0)
            
            self.status_label.config(text="● CONNECTING...", fg="#f39c12")
            self.info_label.config(text=f"Connecting to {host}:{port}...")
            self.root.update()
            
            self.socket.connect((host, port))
            
            # Enable TCP_NODELAY for lower latency
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # Increase buffer sizes
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
            
            self.socket.send(password.encode())
            response = self.socket.recv(1024).decode()
            
            if response != "OK":
                messagebox.showerror("Authentication Failed", "Invalid password")
                self.socket.close()
                self.socket = None
                self.status_label.config(text="● DISCONNECTED", fg="#e74c3c")
                self.info_label.config(text="Authentication failed")
                return
            
            self.connected = True
            self.status_label.config(text="● CONNECTED", fg="#27ae60")
            self.info_label.config(text=f"Connected to {host}:{port}")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            
            # Start receiving screen data
            threading.Thread(target=self.receive_screen, daemon=True).start()
            
            messagebox.showinfo("Connected", f"Successfully connected to {host}\n\nYou can now control the remote computer.")
            
        except socket.timeout:
            messagebox.showerror("Connection Timeout", 
                               f"Could not connect to {host}:{port}\n\n"
                               "Check:\n• Server IP address\n• Server is running\n• Firewall settings\n• Network connection")
            self.status_label.config(text="● DISCONNECTED", fg="#e74c3c")
            self.info_label.config(text="Connection timeout")
        except ConnectionRefusedError:
            messagebox.showerror("Connection Refused", 
                               f"Connection refused by {host}:{port}\n\n"
                               "Make sure:\n• Server is running\n• Port is correct\n• Firewall allows connections")
            self.status_label.config(text="● DISCONNECTED", fg="#e74c3c")
            self.info_label.config(text="Connection refused")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.status_label.config(text="● DISCONNECTED", fg="#e74c3c")
            self.info_label.config(text=f"Error: {str(e)}")

    def disconnect(self):
        self.connected = False
        try:
            if self.socket:
                # Send disconnect command
                data = pickle.dumps({'type': 'disconnect'})
                size = struct.pack("!I", len(data))
                self.socket.sendall(size + data)
                time.sleep(0.1)
        except:
            pass
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
                
            self.status_label.config(text="● DISCONNECTED", fg="#e74c3c")
            self.info_label.config(text="Not connected")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            
            # Clear screen
            if self.canvas:
                self.canvas.delete("all")
                self.photo_image = None
                self.image_id = None

    def receive_screen(self):
        try:
            while self.connected and self.running:
                try:
                    # Receive size
                    size_data = b""
                    while len(size_data) < 4:
                        chunk = self.socket.recv(4 - len(size_data))
                        if not chunk:
                            break
                        size_data += chunk
                    
                    if len(size_data) < 4:
                        break
                        
                    data_size = struct.unpack("!I", size_data)[0]
                    
                    # Receive image data with larger chunks
                    data = b""
                    while len(data) < data_size:
                        chunk_size = min(65536, data_size - len(data))
                        chunk = self.socket.recv(chunk_size)
                        if not chunk:
                            break
                        data += chunk
                    
                    if len(data) < data_size:
                        break
                    
                    # Decode JPEG image
                    buffer = io.BytesIO(data)
                    img = Image.open(buffer)
                    self.current_image = img
                    
                    # Update UI in main thread
                    self.root.after(0, self.update_screen, img)
                    
                except Exception as e:
                    if self.connected:
                        print(f"Screen receive error: {e}")
                    break
                    
        except Exception as e:
            print(f"Receive thread error: {e}")
        finally:
            if self.connected:
                self.root.after(0, self.disconnect)

    def update_screen(self, img):
        try:
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # Calculate aspect-preserving dimensions
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            canvas_aspect = canvas_width / canvas_height
            
            if canvas_aspect > img_aspect:
                # Fit to height
                new_height = canvas_height
                new_width = int(new_height * img_aspect)
            else:
                # Fit to width
                new_width = canvas_width
                new_height = int(new_width / img_aspect)
            
            # Resize image to fit canvas while preserving aspect ratio
            display_img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)
            
            self.photo_image = ImageTk.PhotoImage(display_img)
            
            # Center the image on canvas
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            
            # Clear canvas and draw new image
            self.canvas.delete("all")
            self.image_id = self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.photo_image)
            
        except Exception as e:
            print(f"Screen update error: {e}")

    def send_command(self, command):
        if self.connected and self.socket:
            try:
                data = pickle.dumps(command, protocol=pickle.HIGHEST_PROTOCOL)
                size = struct.pack("!I", len(data))
                self.socket.sendall(size + data)
            except BrokenPipeError:
                self.root.after(0, self.disconnect)
            except Exception as e:
                print(f"Send command error: {e}")
                self.root.after(0, self.disconnect)

    def on_mouse_move(self, event):
        if not self.connected or not self.current_image:
            return
        
        # Throttle mouse events for performance
        current_time = time.time()
        if current_time - self.last_mouse_time < self.mouse_move_delay:
            return
            
        self.last_mouse_time = current_time
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Get original image dimensions
        img_width, img_height = self.current_image.size
        
        # Calculate aspect ratios
        img_aspect = img_width / img_height
        canvas_aspect = canvas_width / canvas_height
        
        # Calculate displayed image dimensions
        if canvas_aspect > img_aspect:
            display_height = canvas_height
            display_width = int(display_height * img_aspect)
        else:
            display_width = canvas_width
            display_height = int(display_width / img_aspect)
        
        # Calculate image offset (centering)
        x_offset = (canvas_width - display_width) // 2
        y_offset = (canvas_height - display_height) // 2
        
        # Adjust mouse position relative to displayed image
        adjusted_x = event.x - x_offset
        adjusted_y = event.y - y_offset
        
        # Check if mouse is within the displayed image bounds
        if adjusted_x < 0 or adjusted_y < 0 or adjusted_x >= display_width or adjusted_y >= display_height:
            return
        
        # Map to image coordinates
        x = int((adjusted_x / display_width) * img_width)
        y = int((adjusted_y / display_height) * img_height)
        
        # Clamp to image bounds
        x = max(0, min(img_width - 1, x))
        y = max(0, min(img_height - 1, y))
        
        # Only send if position changed
        if abs(x - self.last_mouse_x) > 1 or abs(y - self.last_mouse_y) > 1:
            self.last_mouse_x = x
            self.last_mouse_y = y
            
            self.send_command({
                'type': 'mouse_move', 
                'x': x, 
                'y': y,
                'client_width': img_width,
                'client_height': img_height
            })

    def on_mouse_click(self, event):
        if not self.connected:
            return
        self.send_command({'type': 'mouse_click', 'button': 'left', 'pressed': True})

    def on_mouse_release(self, event):
        if not self.connected:
            return
        self.send_command({'type': 'mouse_click', 'button': 'left', 'pressed': False})

    def on_right_click(self, event):
        if not self.connected:
            return
        self.send_command({'type': 'mouse_click', 'button': 'right', 'pressed': True})

    def on_right_release(self, event):
        if not self.connected:
            return
        self.send_command({'type': 'mouse_click', 'button': 'right', 'pressed': False})

    def on_mouse_scroll(self, event):
        if not self.connected:
            return
        self.send_command({'type': 'mouse_scroll', 'dx': 0, 'dy': event.delta})

    def on_key_press(self, event):
        if not self.connected:
            return
        
        # Handle special keys
        special_keys = {
            'Shift_L': 'shift', 'Shift_R': 'shift',
            'Control_L': 'ctrl', 'Control_R': 'ctrl', 
            'Alt_L': 'alt', 'Alt_R': 'alt',
            'Caps_Lock': 'caps_lock',
            'Tab': 'tab',
            'Return': 'enter',
            'BackSpace': 'backspace',
            'Delete': 'delete',
            'Escape': 'esc',
            'Up': 'up',
            'Down': 'down', 
            'Left': 'left',
            'Right': 'right'
        }
        
        key = special_keys.get(event.keysym, event.char if event.char else event.keysym)
        if key:
            self.send_command({'type': 'key', 'key': key, 'pressed': True})

    def on_key_release(self, event):
        if not self.connected:
            return
            
        special_keys = {
            'Shift_L': 'shift', 'Shift_R': 'shift',
            'Control_L': 'ctrl', 'Control_R': 'ctrl',
            'Alt_L': 'alt', 'Alt_R': 'alt',
            'Caps_Lock': 'caps_lock',
            'Tab': 'tab',
            'Return': 'enter', 
            'BackSpace': 'backspace',
            'Delete': 'delete',
            'Escape': 'esc',
            'Up': 'up',
            'Down': 'down',
            'Left': 'left', 
            'Right': 'right'
        }
        
        key = special_keys.get(event.keysym, event.char if event.char else event.keysym)
        if key:
            self.send_command({'type': 'key', 'key': key, 'pressed': False})

    def on_close(self):
        self.running = False
        self.disconnect()
        self.root.destroy()

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_close()

if __name__ == "__main__":
    client = AbazaClient()
    client.run()