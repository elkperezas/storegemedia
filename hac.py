#!/usr/bin/env python3
"""
Simplified HMI for ChemCorp Reactor
"""

from pymodbus.client import ModbusTcpClient
import time
import os
import sys

class ReactorHMI:
    def __init__(self, host, port=502):
        self.client = ModbusTcpClient(host=host, port=port)
        self.connected = False
        
        # Register addresses
        self.REACTOR_LEVEL = 0
        self.REACTOR_TEMP = 1
        self.REACTOR_PRESSURE = 2
        self.TANK_A_LEVEL = 3
        self.TANK_B_LEVEL = 4
        
        # Coil addresses
        self.VALVE_1 = 0
        self.VALVE_2 = 1
        self.HEATER = 2
        self.EMERGENCY_VENT = 3
        self.COOLING_PUMP = 4
        self.EXPLOSION_FLAG = 5
    
    def connect(self):
        self.connected = self.client.connect()
        return self.connected
    
    def read_registers(self):
        try:
            result = self.client.read_holding_registers(address=0, count=5)
            if not result.isError():
                return result.registers
        except:
            pass
        return [0, 0, 0, 0, 0]
    
    def read_coils(self):
        try:
            result = self.client.read_coils(address=0, count=6)
            if not result.isError():
                return result.bits[:6]
        except:
            pass
        return [False] * 6
    
    def clear_screen(self):
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_status_color(self, value, warning, critical):
        if value >= critical:
            return '\033[91m'  # Red
        elif value >= warning:
            return '\033[93m'  # Yellow
        else:
            return '\033[92m'  # Green
    
    def get_bar(self, value, max_value, width=30):
        filled = int((value / max_value) * width)
        bar = '█' * filled + '░' * (width - filled)
        return bar
    
    def display_status(self):
        registers = self.read_registers()
        coils = self.read_coils()
        
        reactor_level = registers[0]
        reactor_temp = registers[1]
        reactor_pressure = registers[2]
        tank_a_level = registers[3]
        tank_b_level = registers[4]
        
        valve1 = coils[0]
        valve2 = coils[1]
        heater = coils[2]
        vent = coils[3]
        cooling = coils[4]
        
        self.clear_screen()
        
        print("╔" + "═"*78 + "╗")
        print("║" + " "*20 + "CHEMICAL REACTOR CONTROL SYSTEM" + " "*27 + "║")
        print("║" + " "*30 + "ChemCorp Industries" + " "*29 + "║")
        print("╠" + "═"*78 + "╣")
        
        # System diagram
        print("║                                                                              ║")
        print("║   ┌─────────┐         ┌──────────────┐         ┌─────────┐                ║")
        print("║   │ TANK A  │  Valve1 │   REACTOR    │ Valve2  │ TANK B  │                ║")
        print(f"║   │  {tank_a_level:3d}%   │ {'[OPEN]' if valve1 else '[SHUT]'}  │  {reactor_level:3d}% | {reactor_temp:3d}°C │ {'[OPEN]' if valve2 else '[SHUT]'}  │  {tank_b_level:3d}%   │                ║")
        print(f"║   │  (Raw)  │────────→│  {reactor_pressure:3d} PSI     │────────→│(Product)│                ║")
        print("║   └─────────┘         └──────────────┘         └─────────┘                ║")
        print("║                                                                              ║")
        print("╠" + "═"*78 + "╣")
        
        # Tank and Reactor status bars
        for label, value, warn, crit in [
            ("Tank A Level", tank_a_level, 80, 95),
            ("Reactor Level", reactor_level, 70, 85),
            ("Temperature", reactor_temp, 150, 200),
            ("Pressure", reactor_pressure, 100, 150),
            ("Tank B Level", tank_b_level, 80, 95)
        ]:
            color = self.get_status_color(value, warn, crit)
            bar = self.get_bar(value, 100 if "Level" in label else 300 if "Temperature" in label else 200, 30)
            unit = "%" if "Level" in label else "°C" if "Temperature" in label else " PSI"
            print(f"║  {label:<16}: {color}{bar}\033[0m {value:3d}{unit:<3}              ║")
        
        print("╠" + "═"*78 + "╣")
        
        # Control systems status
        print("║  CONTROL SYSTEMS:                                                            ║")
        print(f"║    Valve 1 (A→Reactor):  {'OPEN ' if valve1 else 'CLOSED'}                                          ║")
        print(f"║    Valve 2 (Reactor→B):  {'OPEN ' if valve2 else 'CLOSED'}                                          ║")
        print(f"║    Heater:               {'ON   ' if heater else 'OFF  '}                                          ║")
        print(f"║    Emergency Vent:       {'OPEN ' if vent else 'CLOSED'}                                          ║")
        print(f"║    Cooling Pump:         {'ON   ' if cooling else 'OFF  '}                                          ║")
        
        print("╠" + "═"*78 + "╣")
        print("║  Modbus TCP: Connected  |  Scan Rate: 1s  |  Press Ctrl+C to exit           ║")
        print("╚" + "═"*78 + "╝")
    
    def run(self):
        if not self.connect():
            print("[!] Failed to connect to PLC")
            return
        
        print("[*] Connected to PLC, starting HMI...")
        time.sleep(2)
        
        try:
            while True:
                self.display_status()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] HMI shutting down...")
        finally:
            self.client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 hmi_general.py <PLC_IP> [port]")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 502
    
    hmi = ReactorHMI(host, port)
    hmi.run()
