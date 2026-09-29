import math
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from turtlesim.msg import Pose


ANGLE_TOLERANCE = 0.01
DISTANCE_TOLERANCE = 0.03
TURN_GAIN = 6.0
MAX_TURN = 2.0
LINEAR_GAIN = 2.0
MAX_LINEAR = 1.0
HEADING_GAIN = 4.0
MAX_CORRECTION = 0.35


def wrap_to_pi(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


SEGMENTS = {
    1: [
        (-math.pi / 2, 6.0),
    ],
    0: [
        (0.0, 3.0),
        (-math.pi / 2, 6.0),
        (math.pi, 3.0),
        (math.pi / 2, 6.0),
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
            raise ValueError(f'Unsupported digit: {digit}')

        self.segments = SEGMENTS[digit]
        self.pose = None
        self.index = 0
        self.phase = 'turn'
        self.start = None
        self.finished = False
        self.publisher = self.create_publisher(Twist, f'/{turtle}/cmd_vel', 10)
        self.subscription = self.create_subscription(
            Pose, f'/{turtle}/pose', self.on_pose, 10
        )
        self.timer = self.create_timer(0.05, self.on_timer)

    def on_pose(self, pose):
        self.pose = pose

    def publish_stop(self):
        self.publisher.publish(Twist())

    def on_timer(self):
        if self.pose is None or self.finished:
            self.publish_stop()
            return

        heading, length = self.segments[self.index]

        if self.phase == 'turn':
            error = wrap_to_pi(heading - self.pose.theta)
            if abs(error) <= ANGLE_TOLERANCE:
                self.publish_stop()
                self.start = (self.pose.x, self.pose.y)
                self.phase = 'drive'
                return

            command = Twist()
            command.angular.z = clamp(TURN_GAIN * error, -MAX_TURN, MAX_TURN)
            self.publisher.publish(command)
            return

        distance = math.hypot(
            self.pose.x - self.start[0],
            self.pose.y - self.start[1],
        )
        remaining = length - distance
        if remaining <= DISTANCE_TOLERANCE:
            self.publish_stop()
            self.index += 1
            self.phase = 'turn'
            if self.index == len(self.segments):
                self.finished = True
            return

        error = wrap_to_pi(heading - self.pose.theta)
        command = Twist()
        command.linear.x = min(MAX_LINEAR, LINEAR_GAIN * remaining)
        command.angular.z = clamp(
            HEADING_GAIN * error, -MAX_CORRECTION, MAX_CORRECTION
        )
        self.publisher.publish(command)


def main(args=None):
    rclpy.init(args=args)

    node = DigitDrawer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.publish_stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
