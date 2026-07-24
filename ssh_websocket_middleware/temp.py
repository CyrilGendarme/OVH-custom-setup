import socket

port = 55555

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', port))

print(f"Listening on port {port}...")

while True:
    data, addr = sock.recvfrom(1024)
    print(f"Received message from {addr}: {data.decode()}")