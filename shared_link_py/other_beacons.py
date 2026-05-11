#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from premade_msgs import beacon_msg, SL_beacon_to_7005

from UDPConnection import UdpSender


# ESTOP_BROADCAST_ADDR = '192.168.200.255'
BROADCAST_ADDR = '255.255.255.255'
SL_BROAD_PORT = 7005
ID_BROAD_PORT = 1901

class BeaconNode(Node):
    def __init__(self):
        super().__init__('estop_beacon')

        self._SL_udp = UdpSender(BROADCAST_ADDR, SL_BROAD_PORT, broadcast=True)
        self._ID_udp = UdpSender(BROADCAST_ADDR, ID_BROAD_PORT, local_port=ID_BROAD_PORT, broadcast=True)

        self._beacon_timer = self.create_timer(1.0, self._beacon_timer_cb)

        self.get_logger().info(f"Other beacons initialized")

    def _beacon_timer_cb(self):
        self._send_beacon()

    def _send_beacon(self):
        try:
            for _ in range(3):
                self._SL_udp.send(SL_beacon_to_7005)
                self._ID_udp.send(beacon_msg)
        except OSError as e:
            self.get_logger().warn(f"Beacon send failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(BeaconNode())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
