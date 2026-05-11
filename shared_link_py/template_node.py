#!/usr/bin/env python3

import sys
import tty
import termios
import threading

import rclpy
from rclpy.node import Node
from shared_link_py.msg import KairosValues, VehicleControl
from shared_link_py.srv import GetVehicleControl, SendMsgSet


KEYS = {
    'e': 'start',
    'w': 'forward',
    's': 'brake',
    'k': 'connect',
    'l': 'disconnect',
    'n': 'full_connect',
    'm': 'full_disconnect',
    'p': 'ping'
}


class TemplateNode(Node):
    def __init__(self):
        super().__init__('template_node')

        self._cmd = VehicleControl()

        self._get_ctrl_client = self.create_client(GetVehicleControl, 'get_vehicle_control')
        self._send_msg_set_client = self.create_client(SendMsgSet, 'send_msg_set')

        # Waiting for get_vehicle_control service (waits for shared_link_node)
        while not self._get_ctrl_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Waiting for get_vehicle_control service...')
        future = self._get_ctrl_client.call_async(GetVehicleControl.Request())
        rclpy.spin_until_future_complete(self, future)
        self._cmd = future.result().control

        # Publishers
        self._ctrl_pub = self.create_publisher(VehicleControl, 'vehicle_control', 10)

        # Subscriptions
        self._kairos_sub = self.create_subscription(
            KairosValues, 'kairos_values',
            self._kairos_callback, 10)

        # Initializing keyboard control loop
        self._kb_thread = threading.Thread(target=self._keyboard_loop, daemon=True)
        self._kb_thread.start()
        self.get_logger().info(f'Keyboard controls: {KEYS}')

    # -------------- #
    #    Callbacks
    # -------------- #
    def _kairos_callback(self, msg: KairosValues):
        pass

    # -------------- #
    #    Commands
    # -------------- #
    def _publish(self):
        self._ctrl_pub.publish(self._cmd)

    def start(self):
        self._cmd.veh_motion = 1
        self._publish()

    def forward(self):
        self._cmd.veh_brake = 0
        self._cmd.veh_throttle = 1000
        self._publish()

    def brake(self):
        self._cmd.veh_brake = 100
        self._cmd.veh_throttle = 0
        self._publish()

    def connect(self):
        req = SendMsgSet.Request()
        req.msg_set = SendMsgSet.Request.CONNECT
        self._send_msg_set_client.call_async(req)

    def disconnect(self):
        req = SendMsgSet.Request()
        req.msg_set = SendMsgSet.Request.DISCONNECT
        self._send_msg_set_client.call_async(req)

    def full_disconnect(self):
        req = SendMsgSet.Request()
        req.msg_set = SendMsgSet.Request.FULL_DISCONNECT
        self._send_msg_set_client.call_async(req)

    def full_connect(self):
        req = SendMsgSet.Request()
        req.msg_set = SendMsgSet.Request.FULL_CONNECT
        self._send_msg_set_client.call_async(req)

    def ping(self):
        req = SendMsgSet.Request()
        req.msg_set = SendMsgSet.Request.PING
        self._send_msg_set_client.call_async(req)

    # -------------- #
    #    Keyboard
    # -------------- #
    def _keyboard_loop(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd) # raw mode so keypresses received immediately, no Enter
            while rclpy.ok():
                ch = sys.stdin.read(1).lower()
                if ch == '\x03':  # Ctrl+C
                    break
                action = KEYS.get(ch) # translates character to command name based on dictionary
                if action:
                    self.get_logger().info(f"{ch} pressed, executing {action}")
                    getattr(self, action)() # calls command
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings) # undoes set raw so back to regular terminal mode


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(TemplateNode())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
