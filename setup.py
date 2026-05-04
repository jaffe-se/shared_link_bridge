from setuptools import find_packages, setup

package_name = 'shared_link_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rubicon',
    maintainer_email='jaffe.se@northeastern.edu',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'shared_link_node = shared_link_py.shared_link_node:main',
            'template_node = shared_link_py.template_node:main',
            'estop_beacon = shared_link_py.estop_beacon:main',
        ],
    },
)
