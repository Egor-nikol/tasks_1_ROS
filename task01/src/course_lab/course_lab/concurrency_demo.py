"""Measure timer starvation; same vs different callback groups. Not a FIFO model."""
import argparse,threading,time,statistics
import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor,MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from std_srvs.srv import Trigger

class Demo(Node):
    def __init__(self,mode):
        super().__init__('concurrency_demo',namespace='/demo')
        self.slow_group=MutuallyExclusiveCallbackGroup();self.fast_group=MutuallyExclusiveCallbackGroup()
        self.times=[]
        self.fast=self.create_timer(.05,lambda:self.times.append(time.monotonic()),callback_group=self.fast_group if mode=='multi_split' else self.slow_group)
        self.slow=self.create_timer(1.,self.blocking,callback_group=self.slow_group)
    def blocking(self):
        self.get_logger().info('slow callback START (sleep 450 ms)')
        time.sleep(.45)
        self.get_logger().info('slow callback END')

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['single','multi_same','multi_split'],default='single');a=p.parse_args()
    rclpy.init();n=Demo(a.mode);e=SingleThreadedExecutor() if a.mode=='single' else MultiThreadedExecutor(num_threads=2);e.add_node(n)
    t=threading.Thread(target=e.spin,daemon=True);t.start();time.sleep(6)
    e.shutdown(timeout_sec=2);t.join(2)
    gaps=[b-a for a,b in zip(n.times,n.times[1:])]
    if gaps:print({'mode':a.mode,'callbacks':len(n.times),'median_ms':round(statistics.median(gaps)*1000,1),'max_ms':round(max(gaps)*1000,1)})
    n.destroy_node();rclpy.shutdown()
