import rclpy
from rclpy.node import Node

from shared_link_py.msg import KairosValues, VehicleControl
from shared_link_py.srv import GetVehicleControl


class TemplateNode(Node):
    def __init__(self):
        super().__init__('template_node')

        self._cmd = VehicleControl()

        self._ctrl_pub = self.create_publisher(VehicleControl, 'vehicle_control', 10)

        self._kairos_sub = self.create_subscription(
            KairosValues, 'kairos_values',
            self._kairos_callback, 10)

        self._get_ctrl_client = self.create_client(GetVehicleControl, 'get_vehicle_control')

        while not self._get_ctrl_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().info('Waiting for get_vehicle_control service...')
        
        future = self._get_ctrl_client.call_async(GetVehicleControl.Request())
        rclpy.spin_until_future_complete(self, future)
        self._cmd = future.result().control

    def _kairos_callback(self, msg: KairosValues):
        pass

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


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(TemplateNode())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
