#!/usr/bin/env python3
"""
LVDT Controller GUI for STM32 - Optimized Version
Supports PID tuning, EEPROM operations, and command interface
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime

class LVDTControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LVDT Controller - PID Tuning Interface")
        self.root.geometry("800x550")
        self.root.minsize(700, 500)
        self.root.configure(bg='#1e1e1e')
        
        # Serial connection variables
        self.serial_port = None
        self.is_connected = False
        self.read_thread = None
        self.running = True
        
        # PID values
        self.kp = tk.DoubleVar(value=1000.0)
        self.ki = tk.DoubleVar(value=40.0)
        self.kd = tk.DoubleVar(value=0.10)
        
        # Setup GUI
        self.setup_gui()
        
        # Refresh COM ports
        self.refresh_com_ports()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_gui(self):
        """Setup the main GUI interface"""
        
        # Configure styles for dark theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme colors
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#0d6efd"
        success_color = "#198754"
        danger_color = "#dc3545"
        warning_color = "#ffc107"
        entry_bg = "#2d2d2d"
        
        # Configure styles
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe', background=bg_color, foreground=fg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
        style.configure('TButton', background=accent_color, foreground=fg_color, borderwidth=0, focusthickness=0)
        style.map('TButton', background=[('active', '#0b5ed7'), ('pressed', '#0a58ca')])
        
        # Custom button styles
        style.configure('Success.TButton', background=success_color)
        style.map('Success.TButton', background=[('active', '#157347')])
        
        style.configure('Danger.TButton', background=danger_color)
        style.map('Danger.TButton', background=[('active', '#bb2d3b')])
        
        style.configure('Warning.TButton', background=warning_color, foreground='black')
        style.map('Warning.TButton', background=[('active', '#ffca2c')])
        
        # Configure entry style
        style.configure('TEntry', fieldbackground=entry_bg, foreground=fg_color, borderwidth=1)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ==================== Connection Frame ====================
        conn_frame = ttk.LabelFrame(main_frame, text="Serial Connection", padding="5")
        conn_frame.pack(fill=tk.X, pady=(0, 5))
        
        conn_inner = ttk.Frame(conn_frame)
        conn_inner.pack(fill=tk.X)
        
        ttk.Label(conn_inner, text="COM Port:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_combo = ttk.Combobox(conn_inner, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(conn_inner, text="Baud:").pack(side=tk.LEFT, padx=(0, 5))
        self.baud_combo = ttk.Combobox(conn_inner, values=["9600", "19200", "38400", "57600", "115200"], 
                                       width=8, state="readonly")
        self.baud_combo.set("115200")
        self.baud_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        self.connect_btn = ttk.Button(conn_inner, text="Connect", command=self.toggle_connection, width=10)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.refresh_btn = ttk.Button(conn_inner, text="Refresh", command=self.refresh_com_ports, width=8)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status_label = ttk.Label(conn_inner, text="● Disconnected", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # ==================== PID Tuning Frame (Compact) ====================
        pid_frame = ttk.LabelFrame(main_frame, text="PID Tuning", padding="5")
        pid_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Kp Row - Compact
        kp_row = ttk.Frame(pid_frame)
        kp_row.pack(fill=tk.X, pady=2)
        ttk.Label(kp_row, text="Kp (0-5000):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.kp_entry = ttk.Entry(kp_row, textvariable=self.kp, width=10)
        self.kp_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.kp_scale = ttk.Scale(kp_row, from_=0, to=5000, variable=self.kp, orient=tk.HORIZONTAL, length=200)
        self.kp_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.kp_send_btn = ttk.Button(kp_row, text="Set Kp", command=lambda: self.send_command(f"kp={self.kp.get():.2f}"), width=8)
        self.kp_send_btn.pack(side=tk.LEFT)
        
        # Ki Row - Compact
        ki_row = ttk.Frame(pid_frame)
        ki_row.pack(fill=tk.X, pady=2)
        ttk.Label(ki_row, text="Ki (0-500):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.ki_entry = ttk.Entry(ki_row, textvariable=self.ki, width=10)
        self.ki_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.ki_scale = ttk.Scale(ki_row, from_=0, to=500, variable=self.ki, orient=tk.HORIZONTAL, length=200)
        self.ki_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.ki_send_btn = ttk.Button(ki_row, text="Set Ki", command=lambda: self.send_command(f"ki={self.ki.get():.2f}"), width=8)
        self.ki_send_btn.pack(side=tk.LEFT)
        
        # Kd Row - Compact
        kd_row = ttk.Frame(pid_frame)
        kd_row.pack(fill=tk.X, pady=2)
        ttk.Label(kd_row, text="Kd (0-100):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        self.kd_entry = ttk.Entry(kd_row, textvariable=self.kd, width=10)
        self.kd_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.kd_scale = ttk.Scale(kd_row, from_=0, to=100, variable=self.kd, orient=tk.HORIZONTAL, length=200)
        self.kd_scale.pack(side=tk.LEFT, padx=(0, 5))
        self.kd_send_btn = ttk.Button(kd_row, text="Set Kd", command=lambda: self.send_command(f"kd={self.kd.get():.3f}"), width=8)
        self.kd_send_btn.pack(side=tk.LEFT)
        
        # Set All Button Row
        all_row = ttk.Frame(pid_frame)
        all_row.pack(fill=tk.X, pady=5)
        self.pid_all_btn = ttk.Button(all_row, text="Set All PID Values", 
                                       command=self.set_all_pid,
                                       style='Success.TButton', width=18)
        self.pid_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(all_row, text="Format: kp,ki,kd (comma separated)", foreground="#888888", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # ==================== Control Commands Frame (Compact) ====================
        control_frame = ttk.LabelFrame(main_frame, text="Control Commands", padding="5")
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Buttons in 2 rows - Compact
        btn_frame1 = ttk.Frame(control_frame)
        btn_frame1.pack(fill=tk.X, pady=2)
        
        self.save_btn = ttk.Button(btn_frame1, text="💾 Save to EEPROM", 
                                    command=lambda: self.send_command("save"),
                                    width=18)
        self.save_btn.pack(side=tk.LEFT, padx=3)
        
        self.load_btn = ttk.Button(btn_frame1, text="📂 Load from EEPROM", 
                                    command=lambda: self.send_command("load"),
                                    width=18)
        self.load_btn.pack(side=tk.LEFT, padx=3)
        
        self.status_btn = ttk.Button(btn_frame1, text="📊 Get Status", 
                                      command=lambda: self.send_command("status"),
                                      width=18,
                                      style='Warning.TButton')
        self.status_btn.pack(side=tk.LEFT, padx=3)
        
        btn_frame2 = ttk.Frame(control_frame)
        btn_frame2.pack(fill=tk.X, pady=2)
        
        self.reset_btn = ttk.Button(btn_frame2, text="🔄 Reset to Defaults", 
                                     command=lambda: self.send_command("reset"),
                                     width=18,
                                     style='Danger.TButton')
        self.reset_btn.pack(side=tk.LEFT, padx=3)
        
        self.help_btn = ttk.Button(btn_frame2, text="❓ Help", 
                                    command=lambda: self.send_command("help"),
                                    width=18)
        self.help_btn.pack(side=tk.LEFT, padx=3)
        
        self.clear_console_btn = ttk.Button(btn_frame2, text="🗑 Clear Console", 
                                             command=self.clear_console,
                                             width=18)
        self.clear_console_btn.pack(side=tk.LEFT, padx=3)
        
        # ==================== Console Frame (Larger - 50% more space) ====================
        console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(console_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console_text = scrolledtext.ScrolledText(text_frame, 
                                                       font=("Consolas", 9),
                                                       bg="#0a0a0a", fg="#00ff00",
                                                       insertbackground="white",
                                                       wrap=tk.WORD)
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure console tags
        self.console_text.tag_config("error", foreground="#ff4444")
        self.console_text.tag_config("success", foreground="#44ff44")
        self.console_text.tag_config("info", foreground="#44aaff")
        self.console_text.tag_config("warning", foreground="#ffaa44")
        
        # Log startup message
        self.log_message("LVDT Controller GUI Started", "info")
        self.log_message("Ready to connect to STM32", "info")
        
        # Bind Enter key to send command
        self.kp_entry.bind('<Return>', lambda e: self.send_command(f"kp={self.kp.get():.2f}"))
        self.ki_entry.bind('<Return>', lambda e: self.send_command(f"ki={self.ki.get():.2f}"))
        self.kd_entry.bind('<Return>', lambda e: self.send_command(f"kd={self.kd.get():.3f}"))
        
        # Disable controls initially
        self.set_controls_state(False)
        
    def set_controls_state(self, enabled):
        """Enable or disable control widgets based on connection state"""
        state = tk.NORMAL if enabled else tk.DISABLED
        
        self.kp_send_btn.config(state=state)
        self.ki_send_btn.config(state=state)
        self.kd_send_btn.config(state=state)
        self.pid_all_btn.config(state=state)
        self.save_btn.config(state=state)
        self.load_btn.config(state=state)
        self.status_btn.config(state=state)
        self.reset_btn.config(state=state)
        self.help_btn.config(state=state)
        
        self.kp_entry.config(state=state)
        self.ki_entry.config(state=state)
        self.kd_entry.config(state=state)
        self.kp_scale.config(state=state)
        self.ki_scale.config(state=state)
        self.kd_scale.config(state=state)
        
    def refresh_com_ports(self):
        """Refresh the list of available COM ports"""
        current = self.port_combo.get()
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device}" for port in ports]
        self.port_combo['values'] = port_list
        if port_list and not current:
            self.port_combo.set(port_list[0])
            
    def toggle_connection(self):
        """Connect or disconnect from STM32"""
        if not self.is_connected:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        """Establish serial connection"""
        if not self.port_combo.get():
            messagebox.showwarning("Warning", "Please select a COM port")
            return
            
        port_name = self.port_combo.get()
        baud_rate = int(self.baud_combo.get())
        
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                timeout=1,
                write_timeout=1
            )
            
            self.is_connected = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="● Connected", foreground="green")
            self.set_controls_state(True)
            self.port_combo.config(state="disabled")
            self.baud_combo.config(state="disabled")
            
            self.log_message(f"Connected to {port_name} at {baud_rate} baud", "success")
            
            # Start reading thread
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()
            
            # Flush any pending data
            time.sleep(0.5)
            self.serial_port.reset_input_buffer()
            self.serial_port.reset_output_buffer()
            
            # Send welcome command to get initial response
            time.sleep(0.5)
            self.send_command("help")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.log_message(f"Connection failed: {str(e)}", "error")
            
    def disconnect_serial(self):
        """Close serial connection"""
        self.is_connected = False
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="● Disconnected", foreground="red")
        self.set_controls_state(False)
        self.port_combo.config(state="normal")
        self.baud_combo.config(state="normal")
        
        self.log_message("Disconnected from device", "warning")
        
    def read_serial(self):
        """Read data from serial port continuously"""
        buffer = ""
        while self.is_connected and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    # Read all available data
                    data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # Process complete lines
                    while '\n' in buffer or '\r' in buffer:
                        # Find the next line break
                        line_end = -1
                        if '\n' in buffer:
                            line_end = buffer.find('\n')
                        elif '\r' in buffer:
                            line_end = buffer.find('\r')
                        
                        if line_end >= 0:
                            line = buffer[:line_end].strip()
                            buffer = buffer[line_end + 1:]
                            if line:
                                self.root.after(0, self.process_received_data, line)
                        else:
                            break
                else:
                    time.sleep(0.05)
            except Exception as e:
                if self.is_connected:
                    self.root.after(0, self.log_message, f"Read error: {str(e)}", "error")
                break
                
    def send_command(self, command):
        """Send command to STM32 - uses CR only as terminator"""
        if not self.is_connected or not self.serial_port:
            self.log_message("Not connected - cannot send command", "error")
            return False
            
        try:
            # IMPORTANT: Use carriage return (\r) only as command terminator
            # This matches the STM32 UART handler which expects \r
            cmd_with_cr = command + "\r"
            self.serial_port.write(cmd_with_cr.encode())
            self.log_message(f"Sent: {command}", "info")
            return True
        except Exception as e:
            self.log_message(f"Error sending command: {str(e)}", "error")
            return False
            
    def set_all_pid(self):
        """Send all PID values at once - format: pid=kp,ki,kd"""
        # Format with proper precision - no trailing zeros issues
        command = f"pid={self.kp.get():.2f},{self.ki.get():.2f},{self.kd.get():.3f}"
        self.send_command(command)
        
    def process_received_data(self, data):
        """Process data received from STM32"""
        self.log_message(f"Received: {data}", "info")
        
        # Parse PID values from various response formats
        import re
        
        # Parse Kp from response like "Kp = 1000.00"
        kp_match = re.search(r'Kp\s*=\s*([\d.]+)', data)
        if kp_match:
            val = float(kp_match.group(1))
            self.kp.set(val)
            
        # Parse Ki from response like "Ki = 40.00"
        ki_match = re.search(r'Ki\s*=\s*([\d.]+)', data)
        if ki_match:
            val = float(ki_match.group(1))
            self.ki.set(val)
            
        # Parse Kd from response like "Kd = 0.100"
        kd_match = re.search(r'Kd\s*=\s*([\d.]+)', data)
        if kd_match:
            val = float(kd_match.group(1))
            self.kd.set(val)
            
        # Parse from "PID: Kp=xxx, Ki=xxx, Kd=xxx"
        pid_match = re.search(r'PID:\s*Kp=([\d.]+),\s*Ki=([\d.]+),\s*Kd=([\d.]+)', data)
        if pid_match:
            self.kp.set(float(pid_match.group(1)))
            self.ki.set(float(pid_match.group(2)))
            self.kd.set(float(pid_match.group(3)))
            
        # Parse from "Loaded: Kp=xxx, Ki=xxx, Kd=xxx"
        loaded_match = re.search(r'Loaded:\s*Kp=([\d.]+),\s*Ki=([\d.]+),\s*Kd=([\d.]+)', data)
        if loaded_match:
            self.kp.set(float(loaded_match.group(1)))
            self.ki.set(float(loaded_match.group(2)))
            self.kd.set(float(loaded_match.group(3)))
            
        # Log special messages
        if "saved to EEPROM" in data:
            self.log_message("✓ PID values saved to EEPROM successfully!", "success")
        elif "Reset to defaults" in data:
            self.log_message("✓ PID values reset to defaults", "warning")
            self.kp.set(1000.0)
            self.ki.set(40.0)
            self.kd.set(0.10)
        elif "EEPROM write failed" in data:
            self.log_message("✗ EEPROM write failed!", "error")
        elif "No valid config in EEPROM" in data:
            self.log_message("⚠ No valid configuration found in EEPROM", "warning")
            
    def log_message(self, message, msg_type="info"):
        """Add timestamped message to console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format the message
        if msg_type == "error":
            log_entry = f"[{timestamp}] ❌ {message}\n"
        elif msg_type == "success":
            log_entry = f"[{timestamp}] ✅ {message}\n"
        elif msg_type == "warning":
            log_entry = f"[{timestamp}] ⚠️ {message}\n"
        else:
            log_entry = f"[{timestamp}] ℹ️ {message}\n"
        
        self.console_text.insert(tk.END, log_entry, msg_type)
        self.console_text.see(tk.END)
        
    def clear_console(self):
        """Clear console output"""
        self.console_text.delete(1.0, tk.END)
        self.log_message("Console cleared", "info")
        
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.disconnect_serial()
        self.root.destroy()


def main():
    root = tk.Tk()
    # Set DPI awareness for better display on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = LVDTControllerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()