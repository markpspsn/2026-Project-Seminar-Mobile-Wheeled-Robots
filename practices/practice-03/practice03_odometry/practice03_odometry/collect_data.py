import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import TwistStamped
from rosgraph_msgs.msg import Clock
from tf2_ros import Buffer, TransformListener


def stamp_ns(stamp):
    return stamp.sec * 1000000000 + stamp.nanosec


def get_pose(transform):
    position = transform.transform.translation
    q = transform.transform.rotation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    return position.x, position.y, yaw


def integrate_pose(pose, v, w, dt):
    x, y, yaw = pose
    new_yaw = yaw + w * dt
    if abs(w) < 0.000000001:
        x += v * math.cos(yaw) * dt
        y += v * math.sin(yaw) * dt
    else:
        x += v / w * (math.sin(new_yaw) - math.sin(yaw))
        y += v / w * (math.cos(yaw) - math.cos(new_yaw))
    return x, y, new_yaw


class DataCollector(Node):
    def __init__(self):
        super().__init__('collect_data')
        self.declare_parameter('duration', 120.0)
        self.declare_parameter('output_dir', 'results')
        self.declare_parameter('result_name', 'noise_0')
        self.duration_ns = round(self.get_parameter('duration').value * 1000000000)
        self.output_dir = Path(self.get_parameter('output_dir').value)
        self.result_name = self.get_parameter('result_name').value

        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.create_subscription(Clock, '/clock', self.on_clock, 10)
        self.create_subscription(TwistStamped, '/cmd_vel', self.on_command, 10)
        self.timer = self.create_timer(0.05, self.collect)

        self.sim_time_ns = 0
        self.commands = []
        self.command_index = 0
        self.start_ns = None
        self.last_ns = None
        self.command_pose = None
        self.rows = []
        self.finished = False
        self.get_logger().info('Ожидание времени симуляции, команд и TF...')

    def on_clock(self, message):
        self.sim_time_ns = stamp_ns(message.clock)

    def on_command(self, message):
        time_ns = stamp_ns(message.header.stamp)
        self.commands.append((time_ns, message.twist.linear.x, message.twist.angular.z))

    def integrate_commands(self, target_ns):
        time_ns = self.last_ns
        while time_ns < target_ns:
            while (self.command_index + 1 < len(self.commands) and self.commands[self.command_index + 1][0] <= time_ns):
                self.command_index += 1
            end_ns = target_ns
            if self.command_index + 1 < len(self.commands):
                end_ns = min(end_ns, self.commands[self.command_index + 1][0])
            _, v, w = self.commands[self.command_index]
            dt = (end_ns - time_ns) / 1000000000
            self.command_pose = integrate_pose(self.command_pose, v, w, dt)
            time_ns = end_ns

    def collect(self):
        if not self.commands or self.sim_time_ns == 0:
            return

        if not self.buffer.can_transform('map', 'base_link_gt', Time()):
            return
        if not self.buffer.can_transform('map', 'base_link', Time()):
            return
        gt_latest = self.buffer.lookup_transform('map', 'base_link_gt', Time())
        encoder_latest = self.buffer.lookup_transform('map', 'base_link', Time())
        sample_ns = min(stamp_ns(gt_latest.header.stamp), stamp_ns(encoder_latest.header.stamp), self.sim_time_ns, self.commands[-1][0])
        if sample_ns <= 0 or sample_ns < self.commands[0][0]:
            return
        if self.start_ns is not None:
            sample_ns = min(sample_ns, self.start_ns + self.duration_ns)
            if sample_ns <= self.last_ns:
                return

        sample_time = Time(nanoseconds=sample_ns)
        if not self.buffer.can_transform('map', 'base_link_gt', sample_time):
            return
        if not self.buffer.can_transform('map', 'base_link', sample_time):
            return
        gt = get_pose(self.buffer.lookup_transform('map', 'base_link_gt', sample_time))
        encoder = get_pose(self.buffer.lookup_transform('map', 'base_link', sample_time))

        if self.start_ns is None:
            while (self.command_index + 1 < len(self.commands) and self.commands[self.command_index + 1][0] <= sample_ns):
                self.command_index += 1
            _, v, w = self.commands[self.command_index]
            if v == 0 and w == 0:
                return
            self.start_ns = sample_ns
            self.last_ns = sample_ns
            self.command_pose = gt
            self.get_logger().info('Начат сбор данных.')
        else:
            self.integrate_commands(sample_ns)

        self.last_ns = sample_ns
        self.record(gt, encoder, sample_ns)
        if sample_ns - self.start_ns >= self.duration_ns:
            self.timer.cancel()
            self.save_results()
            self.finished = True

    def record(self, gt, encoder, sample_ns):
        row = {'time_s': (sample_ns - self.start_ns) / 1000000000, 'simulation_time_s': sample_ns / 1000000000}
        for name, pose in [('gt', gt), ('encoder', encoder), ('command', self.command_pose)]:
            row[name + '_x'] = pose[0]
            row[name + '_y'] = pose[1]
            row[name + '_yaw'] = pose[2]
            if name != 'gt':
                row[name + '_position_error'] = math.hypot(pose[0] - gt[0], pose[1] - gt[1])
                angle = pose[2] - gt[2]
                row[name + '_yaw_error'] = abs(math.atan2(math.sin(angle), math.cos(angle)))
        _, v, w = self.commands[self.command_index]
        row['linear_x'] = v
        row['angular_z'] = w
        self.rows.append(row)

    def save_results(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = self.output_dir / (self.result_name + '.csv')
        image_path = self.output_dir / (self.result_name + '.png')
        with csv_path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(self.rows)

        figure, axes = plt.subplots(3, 1, figsize=(9, 12), constrained_layout=True)
        times = [row['time_s'] for row in self.rows]
        for name, label, color in [('gt', 'Ground truth', 'tab:blue'), ('encoder', 'Encoders', 'tab:orange'), ('command', 'Commands', 'tab:green')]:
            xs = [row[name + '_x'] for row in self.rows]
            ys = [row[name + '_y'] for row in self.rows]
            axes[0].plot(xs, ys, label=label, color=color)
            if name != 'gt':
                position_errors = [row[name + '_position_error'] for row in self.rows]
                yaw_errors = [row[name + '_yaw_error'] for row in self.rows]
                axes[1].plot(times, position_errors, label=label, color=color)
                axes[2].plot(times, yaw_errors, label=label, color=color)

        axes[0].set_title('Trajectories')
        axes[0].set_xlabel('X, m')
        axes[0].set_ylabel('Y, m')
        axes[0].set_aspect('equal', adjustable='box')
        axes[1].set_title('Absolute position error relative to ground truth')
        axes[1].set_xlabel('Time from start, s')
        axes[1].set_ylabel('Position error, m')
        axes[2].set_title('Absolute yaw error relative to ground truth')
        axes[2].set_xlabel('Time from start, s')
        axes[2].set_ylabel('Yaw error, rad')
        for axis in axes:
            axis.grid(True)
            axis.legend()
        figure.suptitle(self.result_name)
        figure.savefig(image_path, dpi=150)
        plt.close(figure)
        self.get_logger().info(f'Сбор завершён. Данные: {csv_path}; графики: {image_path}')


def main(args=None):
    rclpy.init(args=args)
    node = DataCollector()
    while rclpy.ok() and not node.finished:
        rclpy.spin_once(node)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
