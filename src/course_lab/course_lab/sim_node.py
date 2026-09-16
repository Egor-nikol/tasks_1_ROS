"""Course simulator. Grading instantiates Simulator(web=False) in a separate container.
No ground-truth topic, reset service, or simulator parameter exposing gift geometry.
"""
import json, math, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose, Color
from shad_interfaces.msg import SensorSample
from .world import World, Area

class Simulator(Node):
    def __init__(self, namespace='/lab', time_scale=1.0, web=False):
        super().__init__('gift_world',namespace=namespace)
        if not 0.1<=time_scale<=4.0: raise ValueError('time_scale must be 0.1..4')
        self.lock=threading.RLock()
        self.world=World((1.,1.,0.),Area(6.,5.,8.,7.))
        self.last_command=time.monotonic()
        self.command_trace=[]; self.path=[]; self.sensors_enabled=True
        self.sequence=0
        self.sample_pub=self.create_publisher(SensorSample,'sample',qos_profile_sensor_data)
        self.pose_pub=self.create_publisher(Pose,'pose',qos_profile_sensor_data)
        self.color_pub=self.create_publisher(Color,'color_sensor',qos_profile_sensor_data)
        self.cmd_sub=self.create_subscription(Twist,'cmd_vel',self.command,10)
        self.timer=self.create_timer(.02/time_scale,self.tick)
        self.http=None
        if web:
            node=self
            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path=='/state':
                        body=json.dumps(node.snapshot()).encode(); mime='application/json'
                    elif self.path in ('/','/index.html'):
                        body=(Path(__file__).parent/'panel.html').read_bytes(); mime='text/html; charset=utf-8'
                    elif self.path=='/health':
                        body=b'ok'; mime='text/plain'
                    else: self.send_error(404); return
                    self.send_response(200); self.send_header('Content-Type',mime)
                    self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body)))
                    self.end_headers(); self.wfile.write(body)
                def log_message(self,*args): pass
            self.http=ThreadingHTTPServer(('0.0.0.0',8081),Handler)
            threading.Thread(target=self.http.serve_forever,daemon=True).start()

    def reset_private(self,pose,gift):
        # Called directly by the trusted evaluator, never available via ROS/HTTP.
        with self.lock:
            self.world=World(pose,gift); self.command_trace=[];self.path=[]
            self.last_command=time.monotonic(); self.sensors_enabled=True

    def command(self,msg):
        with self.lock:
            now=time.monotonic(); self.last_command=now
            self.command_trace.append((now,float(msg.linear.x),float(msg.angular.z)))
            self.command_trace=self.command_trace[-20000:]
            self.world.command(msg.linear.x,msg.angular.z)

    def tick(self):
        with self.lock:
            now=time.monotonic()
            # Independent simulator watchdog. Tests still require a STUDENT zero command.
            if now-self.last_command>.4: self.world.command(0.,0.)
            self.world.step(.02); self.sequence+=1
            p=Pose();p.x=float(self.world.x);p.y=float(self.world.y);p.theta=float(self.world.theta)
            p.linear_velocity=float(self.world.v);p.angular_velocity=float(self.world.w)
            green=self.world.sample(now).green
            c=Color();c.r=0 if green else 240;c.g=255 if green else 243;c.b=0 if green else 249
            if not self.path or math.hypot(p.x-self.path[-1][0],p.y-self.path[-1][1])>.06:
                self.path.append((p.x,p.y));self.path=self.path[-5000:]
            if self.sensors_enabled:
                sample=SensorSample();sample.header.stamp=self.get_clock().now().to_msg()
                sample.header.frame_id='world';sample.sequence=self.sequence;sample.pose=p;sample.color=c
                self.sample_pub.publish(sample);self.pose_pub.publish(p);self.color_pub.publish(c)

    def snapshot(self):
        with self.lock:
            w=self.world
            return {'x':w.x,'y':w.y,'theta':w.theta,'v':w.v,'w':w.w,'distance':w.distance,
                'sim_time':w.sim_time,'sequence':self.sequence,'green':w.sample(time.monotonic()).green,
                'gift':vars(w.gift) if w.gift else None,'path':self.path,
                'namespace':self.get_namespace(),'note':'Debug view only. NOT available in grading.'}

    def destroy_node(self):
        if self.http is not None: self.http.shutdown();self.http.server_close()
        return super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    # CLI ROS namespace remapping overrides /lab.
    node=Simulator(web=True)
    try:rclpy.spin(node)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.shutdown()
