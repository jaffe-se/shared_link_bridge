from typing import Union

from enum import Enum
from dataclasses import dataclass, field, fields

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Empty

from shared_link_py.msg import KairosValues, VehicleControl
from shared_link_py.srv import GetVehicleControl

from UDPConnection import UdpConnection
from premade_msgs import *


class TYPE(Enum):
    INT = 0
    FLOAT = 2
    STRING = 4

@dataclass
class SVField:
    type: int  # 0=long, 2=double, 4=string
    value: Union[int, float, str, None] = None
    updated: bool = False

    def apply(self, raw: str):
        """Parse a raw D field string and apply it to this variable."""
        if raw is None or raw == '':
            return
        if self.type == TYPE.INT:
            self.value = int(float(raw))
        elif self.type == TYPE.FLOAT:
            self.value = float(raw)
        elif self.type == TYPE.STRING:
            self.value = str(raw)
        self.updated = True


@dataclass
class SharedLinkOutbound:
    """OCU -> Vehicle (N list)"""
    video_mux1:   SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_start:    SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_enable:   SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_motion:   SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    joy_steer:    SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    veh_steer:    SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_brake:    SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_throttle: SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_shift:    SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_clutch:   SVField = field(default_factory=lambda: SVField(type=TYPE.INT))


@dataclass
class SharedLinkInbound:
    """Vehicle -> OCU (L list)"""
    AutoGpsHead:       SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    AutoGpsLat:        SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    AutoGpsLon:        SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    AutoGpsVel:        SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    AutoGpsReferences: SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    AutoGpsQuality:    SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    AutoGpsStamp:      SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    pause:             SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    key_on:            SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    eng_enb:           SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    pe7:               SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    bbrake:            SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    fbrake:            SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    steerang:          SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    throttle:          SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    svp_enb_eng:       SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    serialpck:         SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_gear:          SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_state:         SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_estop:         SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    veh_obstacle:      SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    vehicle_bat:       SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))
    run_composite:     SVField = field(default_factory=lambda: SVField(type=TYPE.STRING))
    VehicleName:       SVField = field(default_factory=lambda: SVField(type=TYPE.STRING))
    Health_total:      SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    rpm:               SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    fuel:              SVField = field(default_factory=lambda: SVField(type=TYPE.INT))
    sys_thd:           SVField = field(default_factory=lambda: SVField(type=TYPE.FLOAT))

INBOUND_TO_ROS = {
    'AutoGpsHead':       'auto_gps_head',
    'AutoGpsLat':        'auto_gps_lat',
    'AutoGpsLon':        'auto_gps_lon',
    'AutoGpsVel':        'auto_gps_vel',
    'AutoGpsReferences': 'auto_gps_references',
    'AutoGpsQuality':    'auto_gps_quality',
    'AutoGpsStamp':      'auto_gps_stamp',
    'VehicleName':       'vehicle_name',
    'Health_total':      'health_total',
}

class SharedLinkNode(Node):
    def __init__(self):
        super().__init__('shared_link_node')
        self._update_rate = 0.1  # seconds (100ms)
        self._outbound = SharedLinkOutbound()
        self._inbound = SharedLinkInbound()
        self._udp = UdpConnection(KAIROS_IP, KAIROS_PORT, LOCAL_PORT, self._msg_parser)

        self._kairos_pub = self.create_publisher(KairosValues, 'kairos_values', 10)

        self._get_ctrl_srv = self.create_service(
            GetVehicleControl, 'get_vehicle_control',
            self._get_vehicle_control_callback)

        self._vehicle_ctrl_sub = self.create_subscription(
            VehicleControl, 'vehicle_control',
            self._vehicle_control_callback, 10)

        self._field_update_sub = self.create_subscription(
            String, 'field_update',
            self._field_update_callback, 10)

        self._update_timer = self.create_timer(self._update_rate, self._timer_callback)

        self._inbound_count = 0

    # -------------- #
    #      ROS
    # -------------- #
    ### PUBLISHERS
    def _publish_kairos_values(self):
        ros_msg = KairosValues()
        for f in fields(self._inbound):
            sv: SVField = getattr(self._inbound, f.name)
            ros_field = INBOUND_TO_ROS.get(f.name, f.name) # Swaps for ROS name, or leaves as is if not on list
            setattr(ros_msg, ros_field, sv.value)
        self._kairos_pub.publish(ros_msg)

    ### SUBSCRIBERS
    def _vehicle_control_callback(self, msg: VehicleControl):
        for f in fields(self._outbound):
            sv: SVField = getattr(self._outbound, f.name)
            sv.apply(str(getattr(msg, f.name)))

    def _field_update_callback(self, msg: String):
        raw = msg.data
        if ':' not in raw:
            return
        name, value_str = raw.split(':', 1)
        sv = self.get_outbound_field(name)
        if sv is None:
            return
        sv.apply(value_str)


    ### SERVICES
    def _get_vehicle_control_callback(self, request, response: GetVehicleControl.Response):
        for f in fields(self._outbound):
            sv: SVField = getattr(self._outbound, f.name)
            if sv.value is not None:
                setattr(response.control, f.name, sv.value)
        return response

    def _connect_callback(self, request, response: Empty.response):
        self.sendMsg(declare_myIP_msg)
        self.sendMsgs(enab_msgs)
        self.sendMsgs(list_SVs_msgs)
        self.sendMsg(teleop_start)
        
    def _disconnect_callback(self, request, response: Empty.response):
        self.sendMsg(teleop_start)
        self.sendMsgs(term_msgs)


    ### TIMER
    def _timer_callback(self):
        self._inbound_count += 1
        if self._inbound_count < int(1.0 / self._update_rate):
            self.send_data()
        else:
            self.send_data(delta_only=False)
            self._inbound_count = 0

    # -------------- #
    #      UDP
    # -------------- #
    ### ON RECEIVE
    def _msg_parser(self, data_raw, addr):
        # was getting error that it couldn't decode xff, but it also wasn't
        if data_raw[1:4] == b'\xff\xd8\xff':
            print("Seems to be a JPEG")
        else:
            data = data_raw.decode("utf-8")

            if data[:5] != "[:AB|":
                print("Data isn't in SharedLink form")
                print(data)
                return

            split_data = data[1:-1].split("|")

            # assume that checksum is always right because sent over UDP
            # assert calcCheckSum(data[1:-3]) == data[-3:-1]

            match split_data[1]:
                case "N0":
                    match split_data[2][0]:
                        case "D":
                            self._apply_inbound_data(split_data[2:-1])
                        case "R":
                            print("Received R type:")
                            print(data)
                        case _:
                            print(f"Received N0 then {split_data[2]}")
                            print(data)
                case "P0":
                    self.sendMsg(pong_msg)
                case "G0":
                    print("Received Pong Message (ping ACK)")
                case _:
                    print(f"Received {split_data[1]} msg")

    ### SEND
    def send_data(self, delta_only: bool = True):
        msg = ':BA|N0|'
        for f in fields(self._outbound):
            sv: SVField = getattr(self._outbound, f.name)
            if not delta_only or sv.updated:
                msg += f'D{sv.value}|'
                sv.updated = False
            else:
                msg += 'D|'
        msg += 'C'
        self.sendMsg(msg)

    # -------------- #
    #    INTERNALS
    # -------------- #
    def _apply_inbound_data(self, d_fields: list[str]):
        for i, f in enumerate(fields(self._inbound)):
            sv: SVField = getattr(self._inbound, f.name)
            sv.apply(d_fields[i][1:])  # strip leading 'D'
        self._publish_kairos_values()

    def get_outbound_field(self, name: str) -> SVField | None:
        if hasattr(self._outbound, name):
            return getattr(self._outbound, name)
        return None

    ### Utilities

    def sendMsg(self, msg: str) -> None:
        self._udp.send(self._prep_for_send(msg))
    
    def sendMsgs(self, msgs: list):
        for msg in msgs:
            self.sendMsg(msg)

    def get_checksum(self, s: str) -> str:
        return f'{sum(ord(c) for c in s) % 0x100:X}'
    
    def _prep_for_send(self, msg: str) -> str:
        return f"[{msg}{self.get_checksum(msg)}]"
    


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(SharedLinkNode())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
