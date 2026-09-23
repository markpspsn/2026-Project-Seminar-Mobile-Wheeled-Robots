"""Draw one digit with one turtlesim turtle, using its measured pose."""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from turtlesim.msg import Pose


def angle_error(target, current):
    """Signed shortest turn to the absolute heading, in radians."""
    return math.atan2(math.sin(target - current), math.cos(target - current))


# Each (absolute heading in radians, length) is a straight segment.
# Turtle positions are set by scene_setup: 1 begins at (3, 8), 2 at (6, 8).
SEGMENTS = {
    1: [(-math.pi / 2, 3.0), (-math.pi / 2, 3.0)],
    2: [
        (0.0, 3.0),             # top: left to right
        (-math.pi / 2, 3.0),    # upper right
        (math.pi, 3.0),         # middle: right to left
        (-math.pi / 2, 3.0),    # lower left
        (0.0, 3.0),             # bottom: left to right
    ],
}


class DigitDrawer(Node):
    def __init__(self):
        super().__init__('digit_drawer')
        self.declare_parameter('turtle', 'digit_one')
        self.declare_parameter('digit', 1)

        turtle = self.get_parameter('turtle').value
        digit = int(self.get_parameter('digit').value)
        if digit not in SEGMENTS:
            raise ValueError(f'Only digits {list(SEGMENTS)} are defined; got {digit}')

        self.segments = SEGMENTS[digit]
        self.index = 0
        self.phase = 'turn'
        self.start = None
        self.pose = None

        self.publisher = self.create_publisher(Twist, f'/{turtle}/cmd_vel', 10)
        self.subscription = self.create_subscription(
            Pose, f'/{turtle}/pose', self.on_pose, 10
        )
        self.timer = self.create_timer(0.05, self.on_timer)
        self.get_logger().info(f'Drawing {digit} with {turtle}')

    def on_pose(self, pose):
        self.pose = pose

    def on_timer(self):
        cmd = Twist()
        if self.pose is None or self.index == len(self.segments):
            self.publisher.publish(cmd)
            return

        heading, length = self.segments[self.index]

        if self.phase == 'turn':
            error = angle_error(heading, self.pose.theta)
            if abs(error) < 0.03:
                self.phase = 'drive'
                self.start = (self.pose.x, self.pose.y)
            else:
                cmd.angular.z = max(-2.0, min(2.0, 4.0 * error))
        else:
            distance = math.hypot(
                self.pose.x - self.start[0], self.pose.y - self.start[1]
            )
            remaining = length - distance
            if remaining <= 0.04:
                self.index += 1
                self.phase = 'turn'
                self.start = None
                if self.index == len(self.segments):
                    self.get_logger().info('Digit completed; publishing zero velocity')
            else:
                cmd.linear.x = min(1.2, 2.0 * remaining)

        # A zero Twist at each phase transition stops the previous motion.
        self.publisher.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = DigitDrawer()
    try:
        rclpy.spin(node)
    finally:
        node.publisher.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
