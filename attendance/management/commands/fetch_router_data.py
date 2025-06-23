from django.core.management.base import BaseCommand
from attendance.models import Attendance
import subprocess
import re
from django.utils import timezone
from datetime import datetime
import time
import concurrent.futures

class Command(BaseCommand):
    help = 'Scan network for active devices and update attendance'

    def handle(self, *args, **kwargs):
        try:
            all_found = set()

            self.stdout.write("Scanning ARP table...")
            arp_macs = self.scan_arp_table()
            all_found.update(arp_macs)

            self.stdout.write("\nRunning ping sweep...")
            sweep_macs = self.ping_sweep_scan()
            all_found.update(sweep_macs)

            self.stdout.write("\nScanning known IPs...")
            known_macs = self.scan_known_ips()
            all_found.update(known_macs)

            # ✅ Remove stale records not found now
            self.stdout.write(f"\n🗑️ Cleaning up old MACs not found this scan...")
            Attendance.objects.exclude(mac_address__in=all_found).delete()
            self.stdout.write(self.style.SUCCESS(f"✅ Updated: {len(all_found)} devices active"))

        except Exception as e:
            self.stderr.write(f"Error: {e}")

    def scan_arp_table(self):
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        found = set()
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                mac_match = re.search(r'([0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5})', line)
                if mac_match:
                    mac = mac_match.group(1).upper()
                    if mac not in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00']:
                        Attendance.objects.update_or_create(
                            mac_address=mac,
                            defaults={"last_seen": timezone.now()}
                        )
                        found.add(mac)
        return found

    def ping_sweep_scan(self):
        network_base = "192.168.1"
        found = set()

        def ping_ip(ip):
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return ip
            except:
                pass
            return None

        active_ips = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(ping_ip, f"{network_base}.{i}") for i in range(1, 255)]
            for future in concurrent.futures.as_completed(futures):
                ip = future.result()
                if ip:
                    active_ips.append(ip)

        if active_ips:
            for ip in active_ips:
                subprocess.run(['ping', '-c', '1', ip], capture_output=True)
            time.sleep(2)
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    mac_match = re.search(r'([0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5})', line)
                    if mac_match:
                        mac = mac_match.group(1).upper()
                        if mac not in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00']:
                            Attendance.objects.update_or_create(
                                mac_address=mac,
                                defaults={"last_seen": timezone.now()}
                            )
                            found.add(mac)
        return found

    def scan_known_ips(self):
        known_ips = ['192.168.1.2', '192.168.1.6', '192.168.1.7']
        found = set()
        for ip in known_ips:
            subprocess.run(['ping', '-c', '1', '-W', '1', ip], capture_output=True)
        time.sleep(2)
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                mac_match = re.search(r'([0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5})', line)
                if mac_match:
                    mac = mac_match.group(1).upper()
                    if mac not in ['FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00']:
                        Attendance.objects.update_or_create(
                            mac_address=mac,
                            defaults={"last_seen": timezone.now()}
                        )
                        found.add(mac)
        return found
