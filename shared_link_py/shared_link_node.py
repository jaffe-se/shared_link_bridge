import socket
from dataclasses import dataclass
from typing import Union

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

REMOTE_IP   = '192.168.200.220'
REMOTE_PORT = 4000
LOCAL_PORT  = 4220


class UdpConnection:
    def __init__(self, remote_ip: str, remote_port: int, local_port: int):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('', local_port))
        self._socket.setblocking(False)
        self._remote_addr = (remote_ip, remote_port)

    def __del__(self):
        self._socket.close()

    def send(self, msg: str):
        self._socket.sendto(msg.encode(), self._remote_addr)

    def receive(self) -> str:
        try:
            data, _ = self._socket.recvfrom(1024)
            return data.decode()
        except BlockingIOError:
            return ''


@dataclass
class DataField:
    field_type: type
    value: Union[int, float] = 0
    updated: bool = False

from dataclasses import dataclass, field, fields
from typing import Union

@dataclass
class SVField:
    type: int  # 0=long, 2=double, 4=string
    value: Union[int, float, str, None] = None
    updated: bool = False

    def apply(self, raw: str):
        """Parse a raw D field string and apply it to this variable."""
        if raw is None or raw == '':
            return
        if self.type == 0:
            self.value = int(float(raw))
        elif self.type == 2:
            self.value = float(raw)
        elif self.type == 4:
            self.value = str(raw)
        self.updated = True


@dataclass
class SharedLinkOutbound:
    """OCU -> Vehicle (N list)"""
    video_mux1:   SVField = field(default_factory=lambda: SVField(type=0))
    veh_start:    SVField = field(default_factory=lambda: SVField(type=0))
    veh_enable:   SVField = field(default_factory=lambda: SVField(type=0))
    veh_motion:   SVField = field(default_factory=lambda: SVField(type=0))
    joy_steer:    SVField = field(default_factory=lambda: SVField(type=2))
    veh_steer:    SVField = field(default_factory=lambda: SVField(type=0))
    veh_brake:    SVField = field(default_factory=lambda: SVField(type=0))
    veh_throttle: SVField = field(default_factory=lambda: SVField(type=0))
    veh_shift:    SVField = field(default_factory=lambda: SVField(type=0))
    veh_clutch:   SVField = field(default_factory=lambda: SVField(type=0))


@dataclass
class SharedLinkInbound:
    """Vehicle -> OCU (L list)"""
    AutoGpsHead:       SVField = field(default_factory=lambda: SVField(type=2))
    AutoGpsLat:        SVField = field(default_factory=lambda: SVField(type=2))
    AutoGpsLon:        SVField = field(default_factory=lambda: SVField(type=2))
    AutoGpsVel:        SVField = field(default_factory=lambda: SVField(type=2))
    AutoGpsReferences: SVField = field(default_factory=lambda: SVField(type=0))
    AutoGpsQuality:    SVField = field(default_factory=lambda: SVField(type=0))
    AutoGpsStamp:      SVField = field(default_factory=lambda: SVField(type=2))
    pause:             SVField = field(default_factory=lambda: SVField(type=0))
    key_on:            SVField = field(default_factory=lambda: SVField(type=0))
    eng_enb:           SVField = field(default_factory=lambda: SVField(type=0))
    pe7:               SVField = field(default_factory=lambda: SVField(type=0))
    bbrake:            SVField = field(default_factory=lambda: SVField(type=0))
    fbrake:            SVField = field(default_factory=lambda: SVField(type=0))
    steerang:          SVField = field(default_factory=lambda: SVField(type=2))
    throttle:          SVField = field(default_factory=lambda: SVField(type=0))
    svp_enb_eng:       SVField = field(default_factory=lambda: SVField(type=0))
    serialpck:         SVField = field(default_factory=lambda: SVField(type=0))
    veh_gear:          SVField = field(default_factory=lambda: SVField(type=0))
    veh_state:         SVField = field(default_factory=lambda: SVField(type=0))
    veh_estop:         SVField = field(default_factory=lambda: SVField(type=0))
    veh_obstacle:      SVField = field(default_factory=lambda: SVField(type=0))
    vehicle_bat:       SVField = field(default_factory=lambda: SVField(type=2))
    run_composite:     SVField = field(default_factory=lambda: SVField(type=4))
    VehicleName:       SVField = field(default_factory=lambda: SVField(type=4))
    Health_total:      SVField = field(default_factory=lambda: SVField(type=0))
    rpm:               SVField = field(default_factory=lambda: SVField(type=0))
    fuel:              SVField = field(default_factory=lambda: SVField(type=0))
    sys_thd:           SVField = field(default_factory=lambda: SVField(type=2))

class SharedLinkNode(Node):
    def __init__(self):
        super().__init__('shared_link_node')
        self._count = 0
        self._update_rate = 0.1  # seconds (100ms)
        self._data_fields: list[tuple[str, DataField]] = []
        self._udp = UdpConnection(REMOTE_IP, REMOTE_PORT, LOCAL_PORT)

        self._field_update_sub = self.create_subscription(
            String, 'field_update',
            lambda msg: self.parse_field_update(msg.data), 10)

        self._update_timer = self.create_timer(self._update_rate, self._timer_callback)

    def _timer_callback(self):
        self._count += 1
        if self._count < int(1.0 / self._update_rate):
            self.send_data()
        else:
            self.send_data(delta_only=False)
            self._count = 0

    def send_data(self, delta_only: bool = True):
        msg = '[:BA|N0|'
        for _, field in self._data_fields:
            if not delta_only or field.updated:
                msg += f'D{field.value}|'
            else:
                msg += 'D|'
        msg += 'C'
        msg += self.get_checksum(msg) + ']'
        self._udp.send(msg)

    def receive_data(self) -> str:
        return self._udp.receive()

    def parse_field_update(self, raw: str):
        if ':' not in raw:
            return
        name, value_str = raw.split(':', 1)
        field = self.get_field(name)
        if field is None:
            return
        self.set_field_value(name, field.field_type(value_str))

    def set_field_value(self, name: str, value: Union[int, float]):
        field = self.get_field(name)
        if field is None:
            return
        field.value = value
        field.updated = True

    def get_field(self, name: str) -> DataField | None:
        for field_name, field in self._data_fields:
            if field_name == name:
                return field
        return None

    def get_checksum(self, s: str) -> str:
        return f'{sum(ord(c) for c in s) % 0xFF:X}'


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(SharedLinkNode())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
