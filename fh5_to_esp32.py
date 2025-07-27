import struct
import socket
import json
import time
import os
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

class FH5TelemetryForwarder:
    def __init__(self, listen_port=20055, esp32_ip="192.168.1.100", esp32_port=8080):
        self.listen_port = listen_port
        self.esp32_ip = esp32_ip
        self.esp32_port = esp32_port
        
        # Socket to receive from Forza
        self.forza_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.forza_socket.bind(("127.0.0.1", listen_port))
        
        # Socket to send to ESP32
        self.esp32_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Rich console for display
        self.console = Console()
        self.telemetry_data = {}
        
    def parse_fh5_data(self, data):
        """Parse FH5 telemetry data and return key values"""
        if len(data) < 324:
            return None
            
        telemetry = {
            "speed_ms": struct.unpack("<f", data[256:260])[0],
            "speed_kmh": struct.unpack("<f", data[256:260])[0] * 3.6,
            "rpm": struct.unpack("<f", data[16:20])[0],
            "throttle": struct.unpack("<B", data[315:316])[0],
            "brake": struct.unpack("<B", data[316:317])[0],
            "gear": struct.unpack("<B", data[319:320])[0],  # 307 + 12
            "pos_x": struct.unpack("<f", data[244:248])[0],
            "pos_y": struct.unpack("<f", data[248:252])[0],
            "pos_z": struct.unpack("<f", data[252:256])[0],
            "accel_z": struct.unpack("<f", data[28:32])[0]
        }
        return telemetry
    
    def send_to_esp32(self, telemetry_data):
        """Send telemetry data to ESP32 as JSON"""
        try:
            # Create a copy and adjust gear for display
            esp32_data = telemetry_data.copy()
            
            # Adjust gear: FH5 sends 0=R, 1=N, 2=1st, 3=2nd, etc.
            # We want to send: 0=R, 1=N, 2=1st, 3=2nd, etc. (same as FH5)
            # The ESP32 will display it correctly
            
            json_data = json.dumps(esp32_data)
            self.esp32_socket.sendto(json_data.encode(), (self.esp32_ip, self.esp32_port))
            
            # Debug: Print what we're sending (every 20th packet to avoid spam)
            if hasattr(self, '_packet_count'):
                self._packet_count += 1
            else:
                self._packet_count = 1
                
        except Exception as e:
            self.console.print(f"[red]Error sending to ESP32: {e}[/red]")
    
    def create_telemetry_table(self, telemetry):
        """Create a rich table with telemetry data"""
        table = Table(title="🏎️ Forza Horizon 5 Telemetry", title_style="bold cyan")
        
        # Add columns
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="green", justify="right")
        table.add_column("Unit", style="dim", no_wrap=True)
        
        # Add rows with telemetry data
        table.add_row("Speed", f"{telemetry['speed_kmh']:.1f}", "km/h")
        table.add_row("RPM", f"{telemetry['rpm']:.0f}", "")
        
        # Gear display - send the actual gear number we want to display
        gear = telemetry['gear']
        if gear == 0:
            gear_str = "R"
            display_gear = 0
        elif gear == 1:
            gear_str = "N" 
            display_gear = 1
        else:
            gear_str = str(gear - 1)  # Convert FH5 gear to display gear
            display_gear = gear - 1
        table.add_row("Gear", gear_str, "")
        
        table.add_row("Throttle", f"{telemetry['throttle']}", "%")
        table.add_row("Brake", f"{telemetry['brake']}", "%")
        table.add_row("Acceleration Z", f"{telemetry['accel_z']:.2f}", "m/s²")
        
        # Position data
        table.add_row("Position X", f"{telemetry['pos_x']:.1f}", "m")
        table.add_row("Position Y", f"{telemetry['pos_y']:.1f}", "m")
        table.add_row("Position Z", f"{telemetry['pos_z']:.1f}", "m")
        
        return table
    
    def create_status_panel(self):
        """Create a status panel with connection info"""
        status_text = f"""
[bold green]FH5 Telemetry Forwarder Active[/bold green]

📡 Listening: 127.0.0.1:{self.listen_port} (FH5)
📤 Forwarding to: {self.esp32_ip}:{self.esp32_port} (ESP32)

Press Ctrl+C to stop
        """
        return Panel(status_text.strip(), title="Status", border_style="blue")
    
    def test_esp32_connection(self):
        """Test if ESP32 is reachable"""
        try:
            test_data = {"test": "ping", "speed_kmh": 0, "rpm": 0, "gear": 1, "throttle": 0, "brake": 0, "accel_z": 0}
            json_data = json.dumps(test_data)
            self.esp32_socket.sendto(json_data.encode(), (self.esp32_ip, self.esp32_port))
            self.console.print(f"[green]Test packet sent to ESP32 at {self.esp32_ip}:{self.esp32_port}[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]Cannot reach ESP32 at {self.esp32_ip}:{self.esp32_port} - {e}[/red]")
            return False

    def start(self):
        """Start the telemetry forwarder with rich display"""
        self.console.print(self.create_status_panel())
        
        # Test ESP32 connection first
        self.console.print("\n[yellow]Testing ESP32 connection...[/yellow]")
        if not self.test_esp32_connection():
            self.console.print("[red]ESP32 connection test failed. Check IP address and ensure ESP32 is running.[/red]")
            return
        
        self.console.print("\n[yellow]Waiting for telemetry data...[/yellow]\n")
        
        # Initialize with empty data
        empty_telemetry = {
            "speed_kmh": 0.0, "rpm": 0.0, "gear": 1, "throttle": 0, "brake": 0,
            "accel_z": 0.0, "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0
        }
        
        with Live(self.create_telemetry_table(empty_telemetry), refresh_per_second=10) as live:
            while True:
                try:
                    data, addr = self.forza_socket.recvfrom(1024)
                    telemetry = self.parse_fh5_data(data)
                    
                    if telemetry:
                        self.telemetry_data = telemetry
                        self.send_to_esp32(telemetry)
                        
                        # Update the live display
                        live.update(self.create_telemetry_table(telemetry))
                        
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Shutting down...[/yellow]")
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    # Install rich if not already installed
    try:
        from rich.console import Console
    except ImportError:
        print("Installing rich library...")
        os.system("pip install rich")
        from rich.console import Console
    
    # Change ESP32_IP to your ESP32's IP address
    forwarder = FH5TelemetryForwarder(esp32_ip="192.168.1.149")  # Update this IP
    forwarder.start()
