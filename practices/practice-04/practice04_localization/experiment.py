import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, TwistStamped
from lifecycle_msgs.srv import GetState
from rclpy.node import Node
from rclpy.time import Time
from std_srvs.srv import Empty
from tf2_ros import Buffer, TransformListener


def yaw(rotation):
    return math.atan2(
        2.0 * (rotation.w * rotation.z + rotation.x * rotation.y),
        1.0 - 2.0 * (rotation.y * rotation.y + rotation.z * rotation.z),
    )


class Experiment(Node):
    def __init__(self):
        super().__init__('localization_experiment')
        defaults = {
            'localization_mode': 'global',
            'error_x': 0.1,
            'error_y': -0.1,
            'error_yaw': 0.2,
            'min_particles': 500,
            'max_particles': 1000,
            'duration': 240.0,
            'position_threshold': 0.15,
            'angle_threshold': 0.15,
            'confirmation_time': 10.0,
            'results_dir': 'results',
            'run_name': 'global_low',
        }
        self.settings = {}
        for name, value in defaults.items():
            self.declare_parameter(name, value)
            self.settings[name] = self.get_parameter(name).value
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.velocity_publisher = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.initial_pose_publisher = self.create_publisher(
            PoseWithCovarianceStamped, '/initialpose', 10
        )
        self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.receive_estimate, 10
        )
        self.state_client = self.create_client(GetState, '/amcl/get_state')
        self.global_client = self.create_client(Empty, '/reinitialize_global_localization')
        self.state_future = None
        self.global_future = None
        self.active = False
        self.initialized = False
        self.initialization_time = None
        self.start_time = None
        self.last_sample_time = None
        self.interval_start = None
        self.convergence_time = None
        self.rows = []
        self.finished = False
        self.create_timer(0.1, self.step)

    def receive_estimate(self, message):
        stamp = message.header.stamp.sec + message.header.stamp.nanosec / 1e9
        if self.initialized and self.start_time is None and stamp >= self.initialization_time:
            self.start_time = self.get_clock().now().nanoseconds / 1e9
            self.get_logger().info('Experiment started at simulation time %.3f' % self.start_time)

    def initialize(self, now):
        if not self.active:
            if self.state_future is None and self.state_client.service_is_ready():
                self.state_future = self.state_client.call_async(GetState.Request())
            if self.state_future is not None and self.state_future.done():
                self.active = self.state_future.result().current_state.id == 3
                self.state_future = None
            return
        if not self.buffer.can_transform('odom', 'base_link', Time()):
            return
        if self.velocity_publisher.get_subscription_count() == 0:
            return
        if self.settings['localization_mode'] == 'initial':
            if self.initial_pose_publisher.get_subscription_count() == 0:
                return
            message = PoseWithCovarianceStamped()
            message.header.stamp = self.buffer.lookup_transform('odom', 'base_link', Time()).header.stamp
            message.header.frame_id = 'map'
            message.pose.pose.position.x = self.settings['error_x']
            message.pose.pose.position.y = -2.2 + self.settings['error_y']
            angle = self.settings['error_yaw']
            message.pose.pose.orientation.z = math.sin(angle / 2.0)
            message.pose.pose.orientation.w = math.cos(angle / 2.0)
            message.pose.covariance[0] = 0.25
            message.pose.covariance[7] = 0.25
            message.pose.covariance[35] = 0.25
            self.initial_pose_publisher.publish(message)
            self.initialized = True
        else:
            if self.global_future is None and self.global_client.service_is_ready():
                self.global_future = self.global_client.call_async(Empty.Request())
            if self.global_future is not None and self.global_future.done():
                self.global_future.result()
                self.initialized = True
        if self.initialized:
            self.initialization_time = self.get_clock().now().nanoseconds / 1e9
            self.get_logger().info('AMCL initialization completed')

    def publish_velocity(self, moving):
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'base_link'
        if moving:
            message.twist.linear.x = 0.176
            message.twist.angular.z = 0.08
        self.velocity_publisher.publish(message)

    def step(self):
        if self.finished:
            return
        now = self.get_clock().now().nanoseconds / 1e9
        if now <= 0.0:
            return
        if not self.initialized:
            self.initialize(now)
            return
        self.publish_velocity(True)
        if self.start_time is None:
            return
        if now - self.start_time >= self.settings['duration']:
            self.publish_velocity(False)
            self.save_results()
            self.finished = True
            return
        if not self.buffer.can_transform('map', 'base_link_gt', Time()):
            return
        if not self.buffer.can_transform('map', 'base_link', Time()):
            return
        gt_latest = self.buffer.lookup_transform('map', 'base_link_gt', Time())
        estimate_latest = self.buffer.lookup_transform('map', 'base_link', Time())
        gt_time = Time.from_msg(gt_latest.header.stamp).nanoseconds
        estimate_time = Time.from_msg(estimate_latest.header.stamp).nanoseconds
        sample_time = min(gt_time, estimate_time) / 1e9
        if sample_time < self.start_time:
            return
        if self.last_sample_time is not None and sample_time - self.last_sample_time < 0.09:
            return
        stamp = Time(seconds=sample_time)
        if not self.buffer.can_transform('map', 'base_link_gt', stamp):
            return
        if not self.buffer.can_transform('map', 'base_link', stamp):
            return
        gt = self.buffer.lookup_transform('map', 'base_link_gt', stamp).transform
        estimate = self.buffer.lookup_transform('map', 'base_link', stamp).transform
        gt_yaw = yaw(gt.rotation)
        estimate_yaw = yaw(estimate.rotation)
        position_error = math.hypot(
            estimate.translation.x - gt.translation.x,
            estimate.translation.y - gt.translation.y,
        )
        difference = estimate_yaw - gt_yaw
        angle_error = abs(math.atan2(math.sin(difference), math.cos(difference)))
        elapsed = sample_time - self.start_time
        if self.last_sample_time is not None and sample_time - self.last_sample_time > 0.3:
            self.interval_start = None
        self.last_sample_time = sample_time
        within_limits = (
            position_error <= self.settings['position_threshold']
            and angle_error <= self.settings['angle_threshold']
        )
        if within_limits:
            if self.interval_start is None:
                self.interval_start = elapsed
            if self.convergence_time is None:
                if elapsed - self.interval_start >= self.settings['confirmation_time']:
                    self.convergence_time = self.interval_start
                    self.get_logger().info(
                        'Convergence confirmed: %.3f s' % self.convergence_time
                    )
        else:
            self.interval_start = None
        self.rows.append([
            sample_time, elapsed, gt.translation.x, gt.translation.y, gt_yaw,
            estimate.translation.x, estimate.translation.y, estimate_yaw,
            position_error, angle_error,
        ])

    def save_results(self):
        directory = Path(self.settings['results_dir']).expanduser()
        directory.mkdir(parents=True, exist_ok=True)
        name = self.settings['run_name']
        with (directory / (name + '.csv')).open('w', newline='') as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerow([
                'simulation_time_s', 'elapsed_s', 'gt_x_m', 'gt_y_m', 'gt_yaw_rad',
                'amcl_x_m', 'amcl_y_m', 'amcl_yaw_rad',
                'position_error_m', 'angle_error_rad',
            ])
            writer.writerows(self.rows)
        summary = dict(self.settings)
        summary['start_time_s'] = self.start_time
        summary['samples'] = len(self.rows)
        summary['convergence_time_s'] = self.convergence_time
        with (directory / (name + '.json')).open('w') as output:
            json.dump(summary, output, indent=2)
            output.write('\n')
        self.draw_graphs(directory / (name + '.png'))
        if self.convergence_time is None:
            self.get_logger().info('Convergence was not confirmed during the experiment')
        self.get_logger().info('Results saved to ' + str(directory / name))

    def draw_graphs(self, path):
        columns = list(zip(*self.rows))
        figure, axes = plt.subplots(3, 1, figsize=(10, 13), constrained_layout=True)
        axes[0].plot(columns[2], columns[3], label='GT', linewidth=2)
        axes[0].plot(columns[5], columns[6], label='AMCL', linewidth=1)
        axes[0].set_aspect('equal', adjustable='datalim')
        axes[0].set_xlabel('X, m')
        axes[0].set_ylabel('Y, m')
        axes[0].set_title('Trajectories: ' + self.settings['run_name'])
        axes[0].legend()
        axes[1].plot(columns[1], columns[8], label='Position error')
        axes[1].axhline(self.settings['position_threshold'], color='tab:red', linestyle='--', label='Threshold')
        axes[1].set_ylabel('Position error, m')
        axes[2].plot(columns[1], columns[9], label='Yaw error')
        axes[2].axhline(self.settings['angle_threshold'], color='tab:red', linestyle='--', label='Threshold')
        axes[2].set_ylabel('Yaw error, rad')
        for axis in axes[1:]:
            axis.set_xlabel('Time from experiment start, s')
            if self.convergence_time is not None:
                axis.axvline(self.convergence_time, color='tab:green', linestyle=':', label='Convergence: %.2f s' % self.convergence_time)
            axis.legend()
        for axis in axes:
            axis.grid(True, alpha=0.3)
        if self.convergence_time is None:
            figure.suptitle('Convergence not confirmed')
        else:
            figure.suptitle('Convergence time: %.2f s' % self.convergence_time)
        figure.savefig(path, dpi=150)
        plt.close(figure)


def main(args=None):
    rclpy.init(args=args)
    node = Experiment()
    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        node.publish_velocity(False)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
