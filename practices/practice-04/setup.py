from setuptools import find_packages, setup
from glob import glob
import os

package_name = "practice04_localization"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'README.md']),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "worlds"),
            glob(os.path.join("worlds", "*.wbt")),
        ),
        (
            os.path.join("share", package_name, "protos"),
            glob(os.path.join("protos", "*.proto")),
        ),
        (
            os.path.join("share", package_name, "maps"),
            glob(os.path.join("maps", "*.pgm")) + glob(os.path.join("maps", "*.yaml")) + glob(os.path.join("maps", "*.png")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob(os.path.join("config", "*.yaml")),
        ),
        (
            os.path.join("share", package_name, "urdf"),
            glob(os.path.join("urdf", "*.urdf")),
        ),
        (
            os.path.join("share", package_name, "rviz"),
            glob(os.path.join("rviz", "*.rviz")),
        ),
        (
            os.path.join("share", package_name, "scripts"),
            glob(os.path.join("scripts", "*.py")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="markpspsn",
    maintainer_email="mark.ps.psn@gmail.com",
    description="Practice 04: AMCL localization and ground truth in Webots",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "experiment = practice04_localization.experiment:main",
        ],
    },
)
