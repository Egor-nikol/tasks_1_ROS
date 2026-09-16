from setuptools import find_packages, setup
setup(name='course_lab', version='0.1.0', packages=find_packages(exclude=['test']),
 data_files=[('share/ament_index/resource_index/packages',['resource/course_lab']),
 ('share/course_lab',['package.xml'])], package_data={'course_lab':['panel.html']}, install_requires=['setuptools'], zip_safe=True,
 maintainer='Course team', maintainer_email='course@example.invalid',
 description='ROS 2 lesson 01', license='MIT',
 entry_points={'console_scripts':['simulator = course_lab.sim_node:main', 'audit = course_lab.audit:main', 'concurrency_demo = course_lab.concurrency_demo:main']})
