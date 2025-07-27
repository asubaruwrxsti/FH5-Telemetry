import struct
import socket
import time
import sys
from rich.live import Live
from rich.table import Table

def listen_and_analyze_fh5(udp_ip, udp_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))

    print(f"Listening on {udp_ip}:{udp_port} for FH5 telemetry data...\n")

    with Live(refresh_per_second=20) as live:
        while True:
            data, addr = sock.recvfrom(1024)

            # Create a table for displaying FH5 telemetry data
            table = Table(title=f"FH5 Telemetry Data from {addr}")
            table.add_column("Field", justify="left")
            table.add_column("Value", justify="right")

            # Based on Forza telemetry mapping for FH5 (324-byte packet with 12-byte offset)
            if len(data) >= 324:
                # Key telemetry values with correct offsets
                acceleration_z = struct.unpack("<f", data[28:32])[0]  # Forward/backward acceleration
                actual_speed = struct.unpack("<f", data[256:260])[0]  # Speed (244 + 12 offset for FH5)
                
                # Wheel rotation speeds (radians/sec)
                wheel_fl = struct.unpack("<f", data[100:104])[0]
                wheel_fr = struct.unpack("<f", data[104:108])[0]
                wheel_rl = struct.unpack("<f", data[108:112])[0]
                wheel_rr = struct.unpack("<f", data[112:116])[0]

                # Position data (with FH5 offset)
                pos_x = struct.unpack("<f", data[244:248])[0]  # 232 + 12
                pos_y = struct.unpack("<f", data[248:252])[0]  # 236 + 12
                pos_z = struct.unpack("<f", data[252:256])[0]  # 240 + 12
                
                # Engine data
                rpm = struct.unpack("<f", data[16:20])[0]
                
                # Controls
                throttle = struct.unpack("<B", data[315:316])[0]  # 303 + 12
                brake = struct.unpack("<B", data[316:317])[0]     # 304 + 12

                # Add data to the table
                table.add_row("Speed (m/s)", f"{actual_speed:.2f}")
                table.add_row("Speed (km/h)", f"{actual_speed * 3.6:.2f}")
                table.add_row("Acceleration Z", f"{acceleration_z:.3f}")
                table.add_row("RPM", f"{rpm:.0f}")
                table.add_row("Throttle", f"{throttle}")
                table.add_row("Brake", f"{brake}")
                table.add_row("Position X", f"{pos_x:.1f}")
                table.add_row("Position Y", f"{pos_y:.1f}")
                table.add_row("Position Z", f"{pos_z:.1f}")
                table.add_row("Wheel FL (rad/s)", f"{wheel_fl:.2f}")
                table.add_row("Wheel FR (rad/s)", f"{wheel_fr:.2f}")
                table.add_row("Wheel RL (rad/s)", f"{wheel_rl:.2f}")
                table.add_row("Wheel RR (rad/s)", f"{wheel_rr:.2f}")
            else:
                table.add_row("Error", f"Packet too small: {len(data)} bytes")

            live.update(table)

if __name__ == "__main__":
    UDP_IP = "127.0.0.1"
    UDP_PORT = 20055
    listen_and_analyze_fh5(UDP_IP, UDP_PORT)
