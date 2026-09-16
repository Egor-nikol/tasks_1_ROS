from setuptools import find_packages, setup
setup(name='hidden_gift', version='0.1.0', packages=find_packages(exclude=['test']),
 data_files=[('share/ament_index/resource_index/packages',['resource/hidden_gift']),
 ('share/hidden_gift',['package.xml'])], install_requires=['setuptools'], zip_safe=True,
 maintainer='Course team', maintainer_email='course@example.invalid',
 description='ROS 2 lesson 01', license='MIT',
 entry_points={'console_scripts':['server = hidden_gift.server:main']})
