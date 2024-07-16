import socket
import threading
import random
import time

# تنظیمات فرستنده
HOST = 'localhost'
PORT = 12345
WINDOW_SIZE = 4
TIMEOUT = 2
P = 0b1011  # Polynomial for CRC-4

# تابع برای محاسبه CRC-4
def calculate_crc(data, poly):
    crc = 0
    for bit in data:
        crc ^= int(bit)
        for _ in range(4):
            if crc & 0b1000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
        crc &= 0b1111
    return crc

# تابع برای ایجاد خطا در داده‌ها
def introduce_error(data):
    data_list = list(data)
    index = random.randint(0, len(data_list) - 1)
    data_list[index] = '1' if data_list[index] == '0' else '0'  # معکوس کردن بیت‌ها برای ایجاد خطا
    return ''.join(data_list)

# تابع برای ارسال بسته‌ها
def send_packet(sock, packet, addr):
    if random.random() < 0.2:  # احتمال خطا در ارسال
        print(f"Original packet introduced: {packet[:4]} {packet[4:-4]} {packet[-4:]}")
        packet = introduce_error(packet)
        print(f"Packet with error introduced: {packet[:4]} {packet[4:-4]} {packet[-4:]}")
    else:
        print(f"Sent packet: {packet[:4]} {packet[4:-4]} {packet[-4:]}")
    sock.sendto(packet.encode(), addr)

# تابع اصلی فرستنده
def transmitter():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    addr = (HOST, PORT + 1)
    
    messages = ["1010", "1101011", "0000", "1100"]
    packets = []

    for i, message in enumerate(messages):
        seq_num = format(i, '04b')
        crc = format(calculate_crc(message, P), '04b')
        packet = seq_num + message + crc
        packets.append(packet)

    base = 0
    next_seq_num = 0
    timer = None

    while base < len(packets):
        while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(packets):
            send_packet(sock, packets[next_seq_num], addr)
            next_seq_num += 1

        if timer is None:
            timer = time.time()

        try:
            sock.settimeout(TIMEOUT - (time.time() - timer))
            ack, _ = sock.recvfrom(1024)
            ack_num = int(ack.decode(), 2)

            if ack_num >= base:
                base = ack_num + 1
                timer = None
                print(f"Received ACK: {ack_num}")
        except socket.timeout:
            print("Timeout, resending packets...")
            next_seq_num = base
            timer = None

    sock.close()

if __name__ == "__main__":
    transmitter_thread = threading.Thread(target=transmitter)
    transmitter_thread.start()
    transmitter_thread.join()
