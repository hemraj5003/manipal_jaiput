from scapy.all import *
import joblib
import pandas as pd
import numpy as np
import psutil
import os
import logging

# Configure logging
log_file = "log.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load AI Model
current_dir = os.path.dirname(os.path.abspath(__file__))  
model_path = os.path.join(current_dir, "firewall.pkl")
model = joblib.load(model_path)


def extract_features(packet):
    """Extracts features from network packets for AI model"""
    features = {
        'protocol_type': packet.proto if IP in packet else 0,
        'flag': packet[TCP].flags if TCP in packet else 0,
        'src_bytes': len(packet.payload) if packet.haslayer(Raw) else 0,
        'dst_bytes': len(packet.payload) if packet.haslayer(Raw) else 0,
        'count': 1,
        'same_srv_rate': 0,
        'diff_srv_rate': 0,
        'dst_host_srv_count': 1,
        'dst_host_same_srv_rate': 0,
        'dst_host_same_src_port_rate': 0
    }
    return features
    

def detect_and_kill_nmap():
    """Detects and kills the nmap process if running"""
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if "nmap" in proc.info['name'].lower():
            logging.warning(f"Detected Nmap process (PID: {proc.info['pid']}) - Terminating...")
            os.kill(proc.info['pid'], 9)


def predict_traffic(packet):
    """Predict if the traffic is malicious or safe"""
    try:
        features = extract_features(packet)
        df = pd.DataFrame([features])  
        prediction = model.predict(df)

        if prediction[0] == 1:  
            alert_msg = f"🚨 ALERT! Malicious Packet Detected from {packet[IP].src}"
            print(alert_msg)
            logging.warning(alert_msg)
            block_ip(packet[IP].src)
            detect_and_kill_nmap()  
        else:
            normal_msg = f"✅ Normal Packet from {packet[IP].src}"
            print(normal_msg)
            logging.info(normal_msg)
    except Exception as e:
        logging.error(f"Error in prediction: {e}")


def block_ip(ip):
    """Block malicious IP using Windows Firewall"""
    command = f'netsh advfirewall firewall add rule name="Blocked IP {ip}" dir=in action=block remoteip={ip}'
    os.system(command)
    block_msg = f"⛔ IP {ip} has been blocked."
    print(block_msg)
    logging.warning(block_msg)


while True:
    try:
        print("🛡️ AI Firewall is running... Press Ctrl+C to stop.")
        sniff(iface="Wi-Fi", prn=predict_traffic, store=0)
    except Exception as e:
        logging.error(f"⚠️ Error: {e}. Restarting sniffing...")
