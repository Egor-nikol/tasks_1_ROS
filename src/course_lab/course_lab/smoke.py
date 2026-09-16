"""Preflight checks actual ROS messages and motion, not just imports."""

import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from shad_interfaces.msg import SensorSample

from .sim_node import Simulator


def main():
    rclpy.init()
    namespace = "/smoke_" + str(int(time.time() * 1000) % 1_000_000)
    simulator = Simulator(namespace, time_scale=1.0, web=False)
    probe = Node("smoke_probe", namespace=namespace)
    samples = []
    probe.create_subscription(
        SensorSample,
        "sample",
        samples.append,
        qos_profile_sensor_data,
    )
    publisher = probe.create_publisher(Twist, "cmd_vel", 10)
    executor = SingleThreadedExecutor()
    executor.add_node(simulator)
    executor.add_node(probe)

    def spin_for(seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            executor.spin_once(timeout_sec=min(0.02, max(0.0, remaining)))

    try:
        deadline = time.monotonic() + 8.0
        while len(samples) < 5 and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.05)
        if len(samples) < 5:
            raise RuntimeError("no headless ROS sensor samples")

        initial_x = samples[-1].pose.x
        command = Twist()
        command.linear.x = 0.5
        for _ in range(10):
            publisher.publish(command)
            spin_for(0.05)
        publisher.publish(Twist())
        spin_for(0.1)

        if samples[-1].pose.x - initial_x < 0.1:
            raise RuntimeError("cmd_vel did not move simulated robot")
        print(
            "PASS: discovery, custom interface, headless simulation, "
            "sensor stream, cmd_vel motion"
        )
        return 0
    finally:
        executor.remove_node(probe)
        executor.remove_node(simulator)
        probe.destroy_node()
        simulator.destroy_node()
        executor.shutdown(timeout_sec=2.0)
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
