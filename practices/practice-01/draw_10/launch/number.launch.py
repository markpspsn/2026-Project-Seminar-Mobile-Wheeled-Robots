"""Launch turtlesim, automatic scene preparation and both digit controllers."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='turtlesim', executable='turtlesim_node', name='turtlesim', output='screen'),
        Node(package='draw_10', executable='scene_setup', name='scene_setup', output='screen'),
        Node(
            package='draw_10', executable='digit_drawer', name='digit_one_drawer',
            parameters=[{'turtle': 'digit_one', 'digit': 1}], output='screen',
        ),
        Node(
            package='draw_10', executable='digit_drawer', name='digit_zero_drawer',
            parameters=[{'turtle': 'digit_zero', 'digit': 0}], output='screen',
        ),
    ])
