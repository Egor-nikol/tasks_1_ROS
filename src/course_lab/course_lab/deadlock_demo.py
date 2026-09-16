"""Run via course demo deadlock: the broken version needs a process timeout."""
import argparse,rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_srvs.srv import Trigger
class Demo(Node):
    def __init__(self,fixed):
        super().__init__('deadlock_demo',namespace='/deadlock')
        self.fixed=fixed;self.server=self.create_service(Trigger,'ping',self.answer)
        self.client=self.create_client(Trigger,'ping');self.timer=self.create_timer(1.,self.call)
    def answer(self,req,res):res.success=True;res.message='pong';return res
    def call(self):
        self.timer.cancel();self.get_logger().info('calling ping')
        if self.fixed:
            f=self.client.call_async(Trigger.Request())
            f.add_done_callback(lambda fut:self.get_logger().info('response: '+fut.result().message))
        else:
            # Same default mutually exclusive group: even 4 threads do not fix it.
            self.client.call(Trigger.Request())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fixed',action='store_true');a=p.parse_args()
    rclpy.init();n=Demo(a.fixed);e=MultiThreadedExecutor(num_threads=4);e.add_node(n);e.spin()
