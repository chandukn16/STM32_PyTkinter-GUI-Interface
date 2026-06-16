import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QGroupBox, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
import threading
import time

class SerialThread(QThread):
    data_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.running = False
        
    def set_serial(self, serial_port):
        self.serial_port = serial_port
        
    def run(self):
        self.running = True
        buffer = ""
        while self.running:
            if self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting:
                        # Read all available data
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        try:
                            decoded = data.decode('utf-8', errors='ignore')
                            buffer += decoded
                            
                            # Process complete lines
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip('\r')
                                if line:
                                    print(f"Received: {line}")
                                    self.data_received.emit(line)
                        except:
                            pass
                except Exception as e:
                    print(f"Read error: {e}")
            self.msleep(10)
    
    def stop(self):
        self.running = False

class STM32Controller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.process_received_data)
        
        # LED state tracking
        self.led_is_on = False
        self.is_toggle_mode = False
        self.toggle_timer = QTimer()
        self.toggle_timer.timeout.connect(self.toggle_led_indicator)
        
        self.init_ui()
        self.refresh_ports()
        
    def init_ui(self):
        self.setWindowTitle('STM32 LED Controller')
        self.setGeometry(100, 100, 600, 500)
        
        # Main style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QGroupBox {
                color: white;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
            QPushButton#btn_on {
                background-color: #198754;
            }
            QPushButton#btn_on:hover {
                background-color: #157347;
            }
            QPushButton#btn_off {
                background-color: #dc3545;
            }
            QPushButton#btn_off:hover {
                background-color: #bb2d3b;
            }
            QPushButton#btn_toggle {
                background-color: #ffc107;
                color: black;
            }
            QPushButton#btn_toggle:hover {
                background-color: #ffca2c;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #555;
                border-radius: 3px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Connection Group
        connection_group = QGroupBox("Serial Connection")
        connection_layout = QHBoxLayout()
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        connection_layout.addWidget(QLabel("COM Port:"))
        connection_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        connection_layout.addWidget(refresh_btn)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_btn)
        
        self.status_label = QLabel("● Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        connection_layout.addWidget(self.status_label)
        
        connection_layout.addStretch()
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # LED Control Group
        led_group = QGroupBox("LED Control")
        led_layout = QHBoxLayout()
        
        self.btn_on = QPushButton("LED ON")
        self.btn_on.setObjectName("btn_on")
        self.btn_on.clicked.connect(lambda: self.send_command("ON"))
        self.btn_on.setEnabled(False)
        led_layout.addWidget(self.btn_on)
        
        self.btn_off = QPushButton("LED OFF")
        self.btn_off.setObjectName("btn_off")
        self.btn_off.clicked.connect(lambda: self.send_command("OFF"))
        self.btn_off.setEnabled(False)
        led_layout.addWidget(self.btn_off)
        
        self.btn_toggle = QPushButton("TOGGLE")
        self.btn_toggle.setObjectName("btn_toggle")
        self.btn_toggle.clicked.connect(lambda: self.send_command("TOGGLE"))
        self.btn_toggle.setEnabled(False)
        led_layout.addWidget(self.btn_toggle)
        
        led_group.setLayout(led_layout)
        main_layout.addWidget(led_group)
        
        # Status Indicators Group
        status_group = QGroupBox("Status Indicators")
        status_layout = QHBoxLayout()
        
        # LED Status
        led_status_widget = QWidget()
        led_status_layout = QVBoxLayout(led_status_widget)
        self.led_indicator = QLabel()
        self.led_indicator.setFixedSize(60, 60)
        self.led_indicator.setStyleSheet("""
            background-color: #555;
            border-radius: 30px;
            border: 2px solid #888;
        """)
        self.led_indicator.setAlignment(Qt.AlignCenter)
        led_status_layout.addWidget(self.led_indicator)
        
        self.led_status_text = QLabel("LED: OFF")
        self.led_status_text.setFont(QFont("Arial", 11, QFont.Bold))
        self.led_status_text.setAlignment(Qt.AlignCenter)
        self.led_status_text.setStyleSheet("color: #ff0000; font-weight: bold;")
        led_status_layout.addWidget(self.led_status_text)
        status_layout.addWidget(led_status_widget)
        
        # Button Status
        button_status_widget = QWidget()
        button_status_layout = QVBoxLayout(button_status_widget)
        self.button_indicator = QLabel()
        self.button_indicator.setFixedSize(60, 60)
        self.button_indicator.setStyleSheet("""
            background-color: #555;
            border-radius: 30px;
            border: 2px solid #888;
        """)
        self.button_indicator.setAlignment(Qt.AlignCenter)
        button_status_layout.addWidget(self.button_indicator)
        
        self.button_status_text = QLabel("BUTTON: RELEASED")
        self.button_status_text.setFont(QFont("Arial", 11, QFont.Bold))
        self.button_status_text.setAlignment(Qt.AlignCenter)
        self.button_status_text.setStyleSheet("color: #888888; font-weight: bold;")
        button_status_layout.addWidget(self.button_status_text)
        status_layout.addWidget(button_status_widget)
        
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # Console Log
        console_group = QGroupBox("Console")
        console_layout = QVBoxLayout()
        self.console_text = QTextEdit()
        self.console_text.setMaximumHeight(150)
        self.console_text.setReadOnly(True)
        console_layout.addWidget(self.console_text)
        console_group.setLayout(console_layout)
        main_layout.addWidget(console_group)
        
        self.log_message("Application started")
        
    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.console_text.append(f"[{timestamp}] {message}")
        
    def refresh_ports(self):
        current_text = self.port_combo.currentText()
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
        if current_text:
            index = self.port_combo.findText(current_text)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
                
    def toggle_connection(self):
        if self.serial_port is None or not self.serial_port.is_open:
            self.connect_serial()
        else:
            self.disconnect_serial()
            
    def connect_serial(self):
        if self.port_combo.currentText() == "":
            QMessageBox.warning(self, "Warning", "Please select a COM port")
            return
            
        port_name = self.port_combo.currentText().split(" - ")[0]
        
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=1,
                write_timeout=1
            )
            
            self.serial_thread.set_serial(self.serial_port)
            self.serial_thread.start()
            
            self.connect_btn.setText("Disconnect")
            self.status_label.setText(f"● Connected to {port_name}")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            
            self.btn_on.setEnabled(True)
            self.btn_off.setEnabled(True)
            self.btn_toggle.setEnabled(True)
            self.port_combo.setEnabled(False)
            
            self.log_message(f"Connected to {port_name} at 115200 baud")
            time.sleep(0.5)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not connect: {str(e)}")
            self.log_message(f"Connection failed: {str(e)}")
            
    def disconnect_serial(self):
        # Stop toggle timer if running
        if self.toggle_timer.isActive():
            self.toggle_timer.stop()
            self.is_toggle_mode = False
            
        self.serial_thread.stop()
        if self.serial_thread.isRunning():
            self.serial_thread.quit()
            self.serial_thread.wait()
            
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        self.serial_port = None
        self.connect_btn.setText("Connect")
        self.status_label.setText("● Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.btn_on.setEnabled(False)
        self.btn_off.setEnabled(False)
        self.btn_toggle.setEnabled(False)
        self.port_combo.setEnabled(True)
        
        # Reset indicators
        self.led_indicator.setStyleSheet("""
            background-color: #555;
            border-radius: 30px;
            border: 2px solid #888;
        """)
        self.led_status_text.setText("LED: UNKNOWN")
        self.led_status_text.setStyleSheet("color: white; font-weight: bold;")
        self.button_indicator.setStyleSheet("""
            background-color: #555;
            border-radius: 30px;
            border: 2px solid #888;
        """)
        self.button_status_text.setText("BUTTON: RELEASED")
        self.button_status_text.setStyleSheet("color: #888888; font-weight: bold;")
        
        self.log_message("Disconnected")

    def send_command(self, command):
        if self.serial_port and self.serial_port.is_open:
            try:
                # Clear any pending data
                self.serial_port.reset_input_buffer()
                
                # Send command with carriage return and newline
                cmd_with_termination = f"{command}\r\n"
                self.serial_port.write(cmd_with_termination.encode())
                self.serial_port.flush()
                self.log_message(f"Sent: {command}")
                print(f"Sent command: {command}")
            except Exception as e:
                self.log_message(f"Error sending command: {str(e)}")
                self.disconnect_serial()
        else:
            self.log_message("Not connected - cannot send command")

    def toggle_led_indicator(self):
        """Toggle the LED indicator state (called by timer in toggle mode)"""
        if self.is_toggle_mode:
            # Toggle the visual state
            self.led_is_on = not self.led_is_on
            
            if self.led_is_on:
                self.led_indicator.setStyleSheet("""
                    background-color: #00ff00;
                    border-radius: 30px;
                    border: 2px solid #00cc00;
                """)
                self.led_status_text.setText("LED: ON")
                self.led_status_text.setStyleSheet("color: #00ff00; font-weight: bold;")
            else:
                self.led_indicator.setStyleSheet("""
                    background-color: #ff0000;
                    border-radius: 30px;
                    border: 2px solid #cc0000;
                """)
                self.led_status_text.setText("LED: OFF")
                self.led_status_text.setStyleSheet("color: #ff0000; font-weight: bold;")

    def start_toggle_mode(self):
        """Start the LED toggle animation"""
        self.is_toggle_mode = True
        self.led_is_on = False  # Start with OFF state
        self.toggle_timer.start(500)  # 500ms interval matching STM32
        self.log_message("LED TOGGLE mode started - indicator blinking at 500ms")

    def stop_toggle_mode(self):
        """Stop the LED toggle animation"""
        if self.toggle_timer.isActive():
            self.toggle_timer.stop()
        self.is_toggle_mode = False

    def update_led_status(self, is_on):
        """Update LED indicator based on state (for non-toggle mode)"""
        # Stop toggle mode if we're receiving explicit ON/OFF commands
        if self.is_toggle_mode:
            self.stop_toggle_mode()
            self.log_message("LED TOGGLE mode stopped")
            
        self.led_is_on = is_on
        if is_on:
            self.led_indicator.setStyleSheet("""
                background-color: #00ff00;
                border-radius: 30px;
                border: 2px solid #00cc00;
            """)
            self.led_status_text.setText("LED: ON")
            self.led_status_text.setStyleSheet("color: #00ff00; font-weight: bold;")
        else:
            self.led_indicator.setStyleSheet("""
                background-color: #ff0000;
                border-radius: 30px;
                border: 2px solid #cc0000;
            """)
            self.led_status_text.setText("LED: OFF")
            self.led_status_text.setStyleSheet("color: #ff0000; font-weight: bold;")

    def update_button_status(self, is_pressed):
        """Update button indicator based on state"""
        if is_pressed:
            self.button_indicator.setStyleSheet("""
                background-color: #ffff00;
                border-radius: 30px;
                border: 2px solid #cccc00;
            """)
            self.button_status_text.setText("BUTTON: PRESSED")
            self.button_status_text.setStyleSheet("color: #ffff00; font-weight: bold;")
        else:
            self.button_indicator.setStyleSheet("""
                background-color: #888888;
                border-radius: 30px;
                border: 2px solid #555;
            """)
            self.button_status_text.setText("BUTTON: RELEASED")
            self.button_status_text.setStyleSheet("color: #888888; font-weight: bold;")

    def process_received_data(self, data):
        self.log_message(f"Received: {data}")
        print(f"Processing: {data}")
        
        # Parse STM32 output format
        # LED responses: "[LED] LED ON", "[LED] LED OFF", "[LED] LED TOGGLING (500ms)"
        # Button responses: "[BTN] BUTTON PRESSED", "[BTN] BUTTON RELEASED"
        
        # Update LED status
        if "[LED] LED ON" in data:
            self.update_led_status(True)
            self.log_message("LED turned ON")
        elif "[LED] LED OFF" in data:
            self.update_led_status(False)
            self.log_message("LED turned OFF")
        elif "[LED] LED TOGGLING" in data:
            # Start the toggle animation in GUI
            self.start_toggle_mode()
            self.log_message("LED entered TOGGLE mode - indicator synced")
        
        # Update button status
        if "[BTN] BUTTON PRESSED" in data:
            self.update_button_status(True)
            self.log_message("Button pressed")
        elif "[BTN] BUTTON RELEASED" in data:
            self.update_button_status(False)
            self.log_message("Button released")
            
    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()

def main():
    app = QApplication(sys.argv)
    controller = STM32Controller()
    controller.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()