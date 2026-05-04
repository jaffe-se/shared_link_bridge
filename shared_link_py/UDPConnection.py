import socket
import threading

def default_on_recv(data_raw, addr):
    data = data_raw.decode()
    
    print(f"From: {addr[0]} / {addr[1]}")
    print(f"Data: {data}")

class UdpConnection:
    def __init__(self, remote_ip: str, remote_port: int, local_port: int, on_recv: callable = default_on_recv, timeout: float = 1.0):
        self._stop_event = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('', local_port))
        self._socket.settimeout(timeout)

        # self._socket.setblocking(False)
        # ^^^
        # alternative to threading solution, but this requires callling a receive method on repeat, checking if there is anything
        # threading allows the on_recv function to be called any time there is a new message
        
        self._buffer_size = 4096

        self._on_recv = on_recv
        self._remote_addr = (remote_ip, remote_port)

        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def __del__(self):
        self._socket.close()

    def stop(self):
        self._stop_event.set()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                data, addr = self._sock.recvfrom(self._buffer_size)
                self._on_recv(data, addr)
            except socket.timeout:
                continue
        self._sock.close()

    def send(self, msg: str):
        self._socket.sendto(msg.encode(), self._remote_addr)