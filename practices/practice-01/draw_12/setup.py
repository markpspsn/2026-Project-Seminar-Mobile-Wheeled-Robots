"""ROS 2 Python package metadata."""

import os
from glob import glob

from setuptools import setup


package_name = 'draw_12'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Arseniy Mukhometov',
    maintainer_email='235694859+markpspsn@users.noreply.github.com',
    description='Pose based turtlesim drawing of variant 12',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'digit_drawer = draw_12.digit_drawer:main',
        'scene_setup = draw_12.scene_setup:main',
    ]},
)
