#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from shared_link_bridge.msg import KairosValues, VehicleControl
from shared_link_bridge.srv import GetVehicleControl, ExecCmd, FieldUpdate

from enum import Enum


# Map Joy.buttons indices to command names (edge-triggered).
# Default layout assumes an Xbox-style controller as published by joy_node.
class BUTTON(Enum):
    A = 0       # A
    B = 1       # B
    X = 2       # X
    Y = 3       # Y
    LB = 4      # LEFT BUMPER (upper)
    RB = 5      # RIGHT BUMPER (upper)
    BACK = 6    # BACK
    START = 7   # START
    LOGI = 8    # CENTER LOGITECH BUTTON
    LJ = 9      # LEFT JOY PRESS
    RJ = 10     # RIGHT JOY PRESS

class AXIS(Enum):
    LX = 0      # LEFT X Axis           1 (left) to -1 (right)
    LY = 1      # LEFT Y Axis           1 (up) to -1 (down)
    LT = 2      # LEFT Trigger          1 (released) to -1 (deperessed)
    RX = 3      # RIGHT X Axis          1 (left) to -1 (right)
    RY = 4      # RIGHT Y Axis          1 (up) to -1 (down)
    RT = 5      # RIGHT Trigger         1 (released) to -1 (deperessed)
    DPX = 6     # D-PAD X Axis          DISCRETE: 1 (left), 0 (released), -1 (right)
    DPY = 7     # D-PAD Y Axis          DISCRETE: 1 (up), 0 (released), -1 (down)


BUTTONS = {
    BUTTON.A:     'start',
    BUTTON.B:     'stop',
    BUTTON.LB:    'connect',
    BUTTON.BACK:  'teleop_stop',
    BUTTON.START: 'teleop_start',
    BUTTON.LOGI:  'ping',
}

# Buttons handled separately (hold/release semantics rather than edge actions).
DEADMAN_BUTTON = BUTTON.RB         # held -> motion enabled
THROTTLE_BOOST_BUTTON = BUTTON.LJ  # held -> boosted throttle scale
STEER_BOOST_BUTTON = BUTTON.RJ     # held -> boosted steering scale

# Continuous control axes.
THROTTLE_AXIS = AXIS.LY   # positive forward, negative brake
STEER_AXIS = AXIS.RX

# Default and boosted scales.
THROTTLE_SCALE = 100
THROTTLE_SCALE_BOOSTED = 800    # 1000 is true max
STEER_SCALE = 100.0
STEER_SCALE_BOOSTED = 400.0     # 450 is true max
BRAKE_MAX = 100                 # 100 is max


class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_teleop')

        self._cmd = VehicleControl()
        self._prev_buttons: list[int] = []

        self._get_ctrl_client = self.create_client(GetVehicleControl, 'get_vehicle_control')
        self._exec_cmd_client = self.create_client(ExecCmd, 'exec_cmd')
        self._field_update_client = self.create_client(FieldUpdate, 'field_update')

        # Waiting for get_vehicle_control service (waits for shared_link_bridge_node)
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
        self._joy_sub = self.create_subscription(
            Joy, 'joy',
            self._joy_callback, 10)

        self.get_logger().info(f'Controller bindings: {BUTTONS}')

    # -------------- #
    #    Callbacks
    # -------------- #
    def _kairos_callback(self, msg: KairosValues):
        pass

    def _joy_callback(self, msg: Joy):
        # Assert controller is sending expected information
        assert len(msg.buttons) == len(BUTTON) and len(msg.axes) == len(AXIS)

        # Edge-triggered button actions
        for btn, action in BUTTONS.items():
            if self._held(msg, btn) and not self._was_held(btn):
                self.get_logger().info(f"{btn.name} pressed, executing {action}")
                getattr(self, action)()

        # Deadman: motion enabled only while held
        deadman = self._held(msg, DEADMAN_BUTTON)
        was_deadman = self._was_held(DEADMAN_BUTTON)
        if deadman and not was_deadman:
            self.start()
        elif not deadman and was_deadman:
            self.stop()

        # Continuous steering
        steer_scale = STEER_SCALE_BOOSTED if self._held(msg, STEER_BOOST_BUTTON) else STEER_SCALE
        self._cmd.joy_steer = msg.axes[STEER_AXIS.value] * steer_scale

        # Throttle / brake
        v = msg.axes[THROTTLE_AXIS.value]
        if v >= 0:
            throttle_scale = THROTTLE_SCALE_BOOSTED if self._held(msg, THROTTLE_BOOST_BUTTON) else THROTTLE_SCALE
            self._cmd.veh_throttle = int(v * throttle_scale)
            self._cmd.veh_brake = 0
        else:
            self._cmd.veh_throttle = 0
            self._cmd.veh_brake = int(-v * BRAKE_MAX)

        self._publish()
        self._prev_buttons = list(msg.buttons)

    def _held(self, msg: Joy, btn: BUTTON) -> bool:
        return btn.value < len(msg.buttons) and msg.buttons[btn.value] == 1

    def _was_held(self, btn: BUTTON) -> bool:
        return btn.value < len(self._prev_buttons) and self._prev_buttons[btn.value] == 1

    # -------------- #
    #    Commands
    # -------------- #
    def _publish(self):
        self._ctrl_pub.publish(self._cmd)

    def start(self):
        # Technically veh_enable can be set to 1 perminently
        # The veh_motion is supposed to be the deadman's switch
        self._cmd.veh_motion = 1
        self._cmd.veh_enable = 1
        self._publish()

    def stop(self):
        self._cmd.veh_motion = 0
        self._cmd.veh_enable = 0
        self._publish()

    def connect(self):
        req = ExecCmd.Request()
        req.cmd = ExecCmd.Request.CONNECT
        self._exec_cmd_client.call_async(req)

    def disconnect(self):
        req = ExecCmd.Request()
        req.cmd = ExecCmd.Request.DISCONNECT
        self._exec_cmd_client.call_async(req)

    def teleop_start(self):
        req = ExecCmd.Request()
        req.cmd = ExecCmd.Request.TELEOP_START
        self._exec_cmd_client.call_async(req)

    def teleop_stop(self):
        req = ExecCmd.Request()
        req.cmd = ExecCmd.Request.TELEOP_STOP
        self._exec_cmd_client.call_async(req)

    def ping(self):
        req = ExecCmd.Request()
        req.cmd = ExecCmd.Request.PING
        self._exec_cmd_client.call_async(req)

    def field_update(self, name: str, value):
        req = FieldUpdate.Request()
        req.name = name
        req.value = str(value)
        self._field_update_client.call_async(req)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(ControllerNode())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
