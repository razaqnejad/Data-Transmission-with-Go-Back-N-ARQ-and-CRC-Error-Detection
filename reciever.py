import socket
import threading

# تنظیمات گیرنده
HOST = 'localhost'
PORT = 12346
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

# تابع برای اصلاح خطا
def attempt_fix(data, poly, expected_crc):
    data_list = list(data)
    for i in range(len(data_list)):
        modified_data = data_list.copy()
        modified_data[i] = '1' if modified_data[i] == '0' else '0'  # معکوس کردن بیت‌ها
        calc_crc = calculate_crc(modified_data, poly)
        if calc_crc == expected_crc:
            return ''.join(modified_data), True
    return data, False

# تابع اصلی گیرنده
def receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))

    expected_seq_num = 0

    while True:
        packet, addr = sock.recvfrom(1024)
        packet = packet.decode()
        seq_num = int(packet[:4], 2)
        data = packet[4:-4]
        received_crc = int(packet[-4:], 2)
        calc_crc = calculate_crc(data, P)

        if calc_crc == received_crc:
            if seq_num == expected_seq_num:
                print(f"Received valid packet: {data}, Seq: {seq_num}, CRC: {format(calc_crc, '04b')}")
                expected_seq_num += 1
                ack = format(seq_num, '04b')
                sock.sendto(ack.encode(), addr)
                print(f"Sent ACK: {ack}")
            else:
                print(f"Out of order packet: {data}, Seq: {seq_num}")
        else:
            print(f"Error in packet: {data}, Seq: {seq_num}, Received CRC: {format(received_crc, '04b')}, Calculated CRC: {format(calc_crc, '04b')}")
            fixed_data, fixed = attempt_fix(data, P, received_crc)
            if fixed:
                print(f"Fixed packet: {fixed_data}, Seq: {seq_num}, CRC: {format(received_crc, '04b')}")
                if seq_num == expected_seq_num:
                    expected_seq_num += 1
                    ack = format(seq_num, '04b')
                    sock.sendto(ack.encode(), addr)
                    print(f"Sent ACK: {ack}")

if __name__ == "__main__":
    receiver_thread = threading.Thread(target=receiver)
    receiver_thread.start()
    receiver_thread.join()
