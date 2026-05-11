import socket
import threading

def default_on_recv(data_raw, addr):
    data = data_raw.decode()

    print(f"From: {addr[0]} / {addr[1]}")
    print(f"Data: {data}")

class UdpReceiver:
    def __init__(self, local_port: int, on_recv: callable = default_on_recv, timeout: float = 1.0):
        self._stop_event = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(timeout)

        try:
            self._socket.bind(('', local_port))
        except OSError:
            print(f"Port {local_port} in use. If you don't know what process is using it run: \"sudo lsof -i :{local_port}\"")
            raise

        self._buffer_size = 4096
        self._on_recv = on_recv

        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def __del__(self):
        self.stop()

    def stop(self):
        self._stop_event.set()
        print(f"Port {self._socket.getsockname()[1]} freed")
        self._socket.close()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                data, addr = self._socket.recvfrom(self._buffer_size)
                self._on_recv(data, addr)
            except socket.timeout:
                continue
            except OSError:  # handles the socket being closed in stop()
                break


class UdpSender:
    def __init__(self, remote_ip: str, remote_port: int, local_port: int = None, broadcast: bool = False):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if broadcast:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if local_port is not None:
            self._socket.bind(('', local_port))
        self._remote_addr = (remote_ip, remote_port)

    def __del__(self):
        self._socket.close()

    def send(self, msg: str):
        self.send_bytes(msg.encode())

    def send_bytes(self, data: bytes):
        self._socket.sendto(data, self._remote_addr)


class UdpConnection:
    def __init__(self, remote_ip: str, remote_port: int, local_port: int, on_recv: callable = default_on_recv, timeout: float = 1.0, broadcast: bool = False):
        self._stop_event = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if broadcast:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.settimeout(timeout)

        try:
            self._socket.bind(('', local_port))
        except OSError:
            print(f"Port {local_port} in use. If you don't know what process is using it run: \"sudo lsof -i :{local_port}\"")
            raise
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
        self.stop()

    def stop(self):
        self._stop_event.set()
        print(f"Port {self._socket.getsockname()[1]} freed")
        self._socket.close()
        

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                data, addr = self._socket.recvfrom(self._buffer_size)
                self._on_recv(data, addr)
            except socket.timeout:
                continue
            except OSError: # handles the socket being closed in the stop function
                break

    def send(self, msg: str):
        self._socket.sendto(msg.encode(), self._remote_addr)

    def send_bytes(self, data: bytes):
        self._socket.sendto(data, self._remote_addr)