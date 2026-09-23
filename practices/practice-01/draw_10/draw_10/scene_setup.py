"""Prepare the turtlesim scene through ROS services after turtlesim starts."""

import math

import rclpy
from rclpy.node import Node
from turtlesim.srv import Kill, Spawn


def main(args=None):
    rclpy.init(args=args)
    node = Node('scene_setup')
    try:
        kill = node.create_client(Kill, '/kill')
        spawn = node.create_client(Spawn, '/spawn')

        for name, client in (('/kill', kill), ('/spawn', spawn)):
            while rclpy.ok() and not client.wait_for_service(timeout_sec=1.0):
                node.get_logger().info(f'Waiting for {name}')

        if not rclpy.ok():
            return

        future = kill.call_async(Kill.Request(name='turtle1'))
        rclpy.spin_until_future_complete(node, future)
        future.result()  # An exception here indicates the scene was not prepared.

        for name, x, heading in (
            ('digit_one', 3.0, -math.pi / 2),
            ('digit_zero', 6.0, 0.0),
        ):
            request = Spawn.Request(x=x, y=8.0, theta=heading, name=name)
            future = spawn.call_async(request)
            rclpy.spin_until_future_complete(node, future)
            result = future.result()
            node.get_logger().info(f'Spawned {result.name} at ({x}, 8)')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
