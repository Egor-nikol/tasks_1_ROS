"""CLI client: prints feedback and supports cancel-after, without nested callback spins."""
import argparse,time,json
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from shad_interfaces.action import ExploreZone

def main():
    p=argparse.ArgumentParser();p.add_argument('--area',type=float,nargs=4,default=[1,1,10,10]);p.add_argument('--namespace',default='/lab')
    p.add_argument('--cancel-after',type=float);p.add_argument('--timeout',type=float,default=310);a=p.parse_args()
    rclpy.init();node=Node('gift_cli',namespace=a.namespace);client=ActionClient(node,ExploreZone,'explore_zone')
    try:
        if not client.wait_for_server(timeout_sec=10):raise RuntimeError('Action server missing: run course build and course run')
        goal=ExploreZone.Goal()
        goal.min_x,goal.min_y,goal.max_x,goal.max_y=map(float,a.area)
        f=client.send_goal_async(goal,feedback_callback=lambda m:print(f'feedback distance={m.feedback.distance_covered:.2f}',flush=True))
        rclpy.spin_until_future_complete(node,f,timeout_sec=5)
        if not f.done():raise TimeoutError('goal acceptance timeout')
        h=f.result()
        if not h.accepted:print('REJECTED');return 2
        print('ACCEPTED',flush=True);result=h.get_result_async();start=time.monotonic();canceled=False
        while rclpy.ok() and not result.done():
            rclpy.spin_once(node,timeout_sec=.05)
            elapsed=time.monotonic()-start
            if a.cancel_after is not None and elapsed>=a.cancel_after and not canceled:
                h.cancel_goal_async();canceled=True;print('CANCEL REQUEST SENT (not terminal yet)',flush=True)
            if elapsed>a.timeout:raise TimeoutError('result timeout')
        r=result.result();print(json.dumps({'status':r.status,'target_found':r.result.target_found,'target_x':r.result.target_x,'target_y':r.result.target_y}))
        return 0
    finally:node.destroy_node();rclpy.shutdown()
if __name__=='__main__':raise SystemExit(main())
