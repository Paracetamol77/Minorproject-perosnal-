from django.core.management.base import BaseCommand
from attendance.models import Attendance
import subprocess
import re
from datetime import datetime
import socket

class Command(BaseCommand):
    help = 'Scan network for active devices and update attendance'

    def handle(self, *args, **kwargs):
        try:
            # Method 1: Use ARP table to find active devices
            self.stdout.write("Scanning network using ARP table...")
            initial_macs = self.scan_arp_table()
            
            # Method 2: Comprehensive ping sweep
            self.ping_sweep_scan()
            
            # Method 3: Direct scan of known active IPs
            self.scan_known_ips()
            
        except Exception as e:
            self.stderr.write(f"Error: {e}")
    
    def scan_arp_table(self):
        """Initial ARP table scan"""
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Parse ARP output to extract MAC addresses
            arp_lines = result.stdout.split('\n')
            macs = []
            
            for line in arp_lines:
                # Look for MAC address pattern (XX:XX:XX:XX:XX:XX)
                mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
                if mac_match:
                    mac = mac_match.group(1).upper()
                    # Skip incomplete entries and invalid MACs
                    if ('incomplete' not in line.lower() and 
                        mac != 'FF:FF:FF:FF:FF:FF' and  # Skip broadcast
                        mac != '00:00:00:00:00:00'):   # Skip null MAC
                        macs.append(mac)
            
            if macs:
                for mac in macs:
                    Attendance.objects.update_or_create(
                        mac_address=mac,
                        defaults={"last_seen": datetime.now()}
                    )
                self.stdout.write(self.style.SUCCESS(f"Updated attendance for {len(macs)} devices using ARP."))
                self.stdout.write(f"Found MACs: {', '.join(macs)}")
                return macs
            else:
                self.stdout.write("No active devices found in ARP table.")
                return []
        return []
    
    def scan_known_ips(self):
        """Scan specific IPs we know are active"""
        self.stdout.write("\n=== SCANNING KNOWN ACTIVE IPs ===")
        known_ips = ['192.168.1.2', '192.168.1.6', '192.168.1.7', '192.168.1.10', '192.168.1.20', '192.168.1.21']
        
        for ip in known_ips:
            try:
                # Try to ping the IP
                result = subprocess.run(['ping', '-c', '2', ip], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    self.stdout.write(f"✅ {ip} is responding")
                else:
                    self.stdout.write(f"❌ {ip} not responding")
            except subprocess.TimeoutExpired:
                self.stdout.write(f"⏰ {ip} timed out")
        
        # Wait and re-scan ARP table
        import time
        time.sleep(3)
        
        # Final ARP scan
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        if result.returncode == 0:
            self.stdout.write("\n=== FINAL ARP TABLE SCAN ===")
            
            arp_lines = result.stdout.split('\n')
            final_macs = []
            
            for line in arp_lines:
                if line.strip():
                    # Extract IP and MAC from each line
                    ip_match = re.search(r'\(([\d.]+)\)', line)
                    mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
                    
                    if ip_match and mac_match:
                        ip = ip_match.group(1)
                        mac = mac_match.group(1).upper()
                        
                        if ('incomplete' not in line.lower() and 
                            mac != 'FF:FF:FF:FF:FF:FF' and 
                            mac != '00:00:00:00:00:00'):
                            
                            self.stdout.write(f"  Device: {mac} at {ip}")
                            if mac not in final_macs:
                                final_macs.append(mac)
            
            # Update attendance for all devices
            if final_macs:
                for mac in final_macs:
                    Attendance.objects.update_or_create(
                        mac_address=mac,
                        defaults={"last_seen": datetime.now()}
                    )
                self.stdout.write(self.style.SUCCESS(f"\n🎯 FINAL RESULT: Found {len(final_macs)} total devices"))
                self.stdout.write(f"All MACs: {', '.join(final_macs)}")
    
    def ping_sweep_scan(self):
        """Comprehensive ping sweep to find ALL devices"""
        self.stdout.write("\nRunning comprehensive ping sweep...")
        
        try:
            network_base = "192.168.1"
            active_ips = []
            
            # Ping ALL possible addresses (1-254)
            self.stdout.write("Pinging all addresses in 192.168.1.x range...")
            
            import concurrent.futures
            import threading
            
            def ping_ip(ip):
                try:
                    result = subprocess.run(['ping', '-c', '1', '-W', '1000', ip], 
                                          capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        return ip
                except:
                    pass
                return None
            
            # Use threading for faster scanning
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                for i in range(1, 255):  # Scan full range
                    ip = f"{network_base}.{i}"
                    futures.append(executor.submit(ping_ip, ip))
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        active_ips.append(result)
            
            active_ips.sort(key=lambda x: int(x.split('.')[-1]))  # Sort by last octet
            
            if active_ips:
                self.stdout.write(f"Found {len(active_ips)} active IPs: {', '.join(active_ips)}")
                
                # Ping each IP again to ensure ARP table is populated
                for ip in active_ips:
                    try:
                        subprocess.run(['ping', '-c', '1', ip], capture_output=True, timeout=5)
                    except subprocess.TimeoutExpired:
                        self.stdout.write(f"Timeout pinging {ip}, but continuing...")
                
                # Wait a moment for ARP table to update
                import time
                time.sleep(2)
                
                # Re-read ARP table for ALL devices
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.stdout.write("\n=== COMPLETE ARP TABLE AFTER PING SWEEP ===")
                    
                    # Parse ARP output again
                    arp_lines = result.stdout.split('\n')
                    all_macs = []
                    
                    for line in arp_lines:
                        if line.strip():
                            # Extract IP and MAC from each line
                            ip_match = re.search(r'\(([\d.]+)\)', line)
                            mac_match = re.search(r'([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})', line)
                            
                            if ip_match and mac_match:
                                ip = ip_match.group(1)
                                mac = mac_match.group(1).upper()
                                
                                if ('incomplete' not in line.lower() and 
                                    mac != 'FF:FF:FF:FF:FF:FF' and 
                                    mac != '00:00:00:00:00:00'):
                                    
                                    self.stdout.write(f"  Found: {mac} at {ip}")
                                    if mac not in all_macs:
                                        all_macs.append(mac)
                    
                    # Update attendance for all found devices
                    if all_macs:
                        for mac in all_macs:
                            Attendance.objects.update_or_create(
                                mac_address=mac,
                                defaults={"last_seen": datetime.now()}
                            )
                        self.stdout.write(self.style.SUCCESS(f"\nTOTAL: Updated attendance for {len(all_macs)} devices after ping sweep."))
                    
            else:
                self.stdout.write("No active IPs found during ping sweep.")
                
        except Exception as e:
            self.stderr.write(f"Ping sweep error: {e}")

    def get_router_info(self):
        """Try to get router information"""
        try:
            # Try to get router info via SNMP (if available)
            result = subprocess.run(['snmpwalk', '-v2c', '-c', 'public', '192.168.1.1'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.stdout.write("Router SNMP info:")
                self.stdout.write(result.stdout[:500])  # First 500 chars
        except:
            pass