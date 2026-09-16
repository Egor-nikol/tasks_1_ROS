"""Black-box ROS tests. Official mode runs in a container with NO student filesystem.
Only the simulator/auditor container can access scene truth and write report.json.
Local tests are formative and explicitly not an authoritative grade.
"""
import argparse, json, math, os, random, signal, subprocess, threading, time, traceback
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from std_srvs.srv import Trigger
from shad_interfaces.action import ExploreZone
from .sim_node import Simulator
from .world import Area

CORE_WEIGHTS={'found':55,'absent':45}
REGRESSION_CASES=('inside','cancel','invalid','busy','feedback_health','sensor_loss','namespace','deadline')
CASE_POINTS={**CORE_WEIGHTS,**{name:0 for name in REGRESSION_CASES}}

def wait_future(f, seconds):
    deadline=time.monotonic()+seconds
    while not f.done() and time.monotonic()<deadline: time.sleep(.01)
    if not f.done():raise AssertionError(f'Future timeout after {seconds}s')
    return f.result()

class Audit(Node):
    def __init__(self, namespace,sim,timeout=95.):
        super().__init__('course_auditor',namespace=namespace)
        self.sim=sim;self.timeout=timeout;self.feedback=[];self.goal_handle=None;self.metrics={}
        self.client=ActionClient(self,ExploreZone,'explore_zone')
        self.health=self.create_client(Trigger,'health')
    def send(self,area,expect=True):
        if not self.client.wait_for_server(timeout_sec=12):raise AssertionError('explore_zone not discovered in requested namespace')
        goal=ExploreZone.Goal()
        goal.min_x,goal.min_y,goal.max_x,goal.max_y=map(float,area)
        f=self.client.send_goal_async(goal,feedback_callback=lambda m:self.feedback.append((time.monotonic(),float(m.feedback.distance_covered))))
        h=wait_future(f,3.)
        if expect and not h.accepted:raise AssertionError('valid goal rejected')
        if h.accepted:self.goal_handle=h
        return h
    def wait_motion(self):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            with self.sim.lock:
                if any(abs(v)+abs(w)>.01 for _,v,w in self.sim.command_trace):return
            time.sleep(.02)
        raise AssertionError('no movement command within 5 s')
    def assert_stopped(self,since):
        terminal_seen=time.monotonic()
        time.sleep(.3)
        with self.sim.lock:
            cmds=[(t,v,w) for t,v,w in self.sim.command_trace if t>=since]
            invalid=self.sim.world.invalid_commands;limited=self.sim.world.limit_violations
        zeros=[t for t,v,w in cmds if abs(v)<1e-6 and abs(w)<1e-6]
        if not zeros:raise AssertionError('no explicit zero Twist; watchdog stopping is NOT enough')
        first=min(zeros)
        if any(abs(v)+abs(w)>1e-5 for t,v,w in cmds if t>terminal_seen+.05):
            raise AssertionError('nonzero command after terminal stop')
        if invalid or limited:raise AssertionError('non-finite/out-of-limit velocity commands')
        self.metrics['explicit_stop']=True
    def cancel(self,h):
        start=time.monotonic();response=wait_future(h.cancel_goal_async(),1.0)
        if not any(bytes(x.goal_id.uuid)==bytes(h.goal_id.uuid) for x in response.goals_canceling):
            raise AssertionError('cancel rejected or requested goal missing from goals_canceling')
        result=wait_future(h.get_result_async(),2.0)
        if result.status!=5 or result.result.target_found:raise AssertionError('expected CANCELED(5), target_found=false')
        self.metrics['cancel_terminal_ms']=round((time.monotonic()-start)*1000,1)
        with self.sim.lock:
            zero=[t for t,v,w in self.sim.command_trace if t>=start and abs(v)+abs(w)<1e-6]
        if not zero or min(zero)-start>.5:raise AssertionError('no student zero command within 500 ms of cancel')
        self.assert_stopped(start)
    def run(self,name,seed):
        rng=random.Random(seed)
        area=(2.,2.,8.,8.)
        gx=rng.uniform(3.,5.);gy=rng.uniform(3.,5.)
        gift=Area(gx,gy,gx+rng.uniform(1.,1.8),gy+rng.uniform(1.,1.8))
        pose=(2.4,2.3,rng.uniform(-math.pi,math.pi))
        if name=='inside':pose=((gift.x0+gift.x1)/2,(gift.y0+gift.y1)/2,1.)
        if name in ('absent','cancel','busy','feedback_health','sensor_loss','deadline'):gift=None
        with self.sim.lock:self.sim.reset_private(pose,gift)
        time.sleep(.5)
        if name=='namespace':
            if not self.client.wait_for_server(timeout_sec=12):raise AssertionError('action absent under arbitrary namespace')
            if not self.health.wait_for_service(timeout_sec=3):raise AssertionError('health service absent under arbitrary namespace')
            response=wait_future(self.health.call_async(Trigger.Request()),.5)
            if not response.success:raise AssertionError('health failed')
            self.metrics['namespace']=self.get_namespace();return
        if name=='invalid':
            for bad in [(9.,2.,1.,3.),(-1.,0.,2.,2.),(float('nan'),0.,3.,3.)]:
                h=self.send(bad,expect=False)
                if h.accepted:raise AssertionError('invalid goal accepted: '+str(bad))
            return
        if name=='deadline':
            from rcl_interfaces.srv import SetParameters
            from rclpy.parameter import Parameter
            setter=self.create_client(SetParameters,'gift_server/set_parameters')
            if not setter.wait_for_service(timeout_sec=12):raise AssertionError('parameter service missing')
            req=SetParameters.Request();req.parameters=[Parameter('task_timeout_sec',value=1.0).to_parameter_msg()]
            response=wait_future(setter.call_async(req),2.)
            if not response.results or not response.results[0].successful:raise AssertionError('cannot set task timeout')
            h=self.send(area);start=time.monotonic();rr=wait_future(h.get_result_async(),2.5)
            if rr.status!=6 or rr.result.target_found:raise AssertionError('deadline must ABORT, not report absence')
            self.assert_stopped(start);return
        h=self.send(area)
        if name in ('cancel','busy','feedback_health','sensor_loss'):self.wait_motion()
        if name=='cancel':self.cancel(h);return
        if name=='busy':
            h2=self.send(area,expect=False)
            if h2.accepted:raise AssertionError('second goal accepted while first active; course policy is REJECT')
            self.cancel(h);return
        if name=='feedback_health':
            if not self.health.wait_for_service(timeout_sec=2):raise AssertionError('health service not found')
            latencies=[]
            for _ in range(6):
                t=time.monotonic();r=wait_future(self.health.call_async(Trigger.Request()),.5)
                if not r.success:raise AssertionError('health response false')
                latencies.append(time.monotonic()-t);time.sleep(.15)
            if len(self.feedback)<3:raise AssertionError('need regular feedback while moving (target 5 Hz)')
            dist=[d for _,d in self.feedback]
            if not all(math.isfinite(d) and d>=0 for d in dist):raise AssertionError('invalid feedback distance')
            if any(b<a-.02 for a,b in zip(dist,dist[1:])):raise AssertionError('feedback distance decreased')
            if max(dist)<=.05:raise AssertionError('feedback reports no travelled distance')
            self.metrics['health_max_ms']=round(max(latencies)*1000,1);self.metrics['feedback_messages']=len(self.feedback)
            self.cancel(h);return
        if name=='sensor_loss':
            start=time.monotonic()
            with self.sim.lock:self.sim.sensors_enabled=False
            result=wait_future(h.get_result_async(),2.0)
            if result.status!=6 or result.result.target_found:raise AssertionError('sensor loss must ABORT(6), not report absence')
            self.assert_stopped(start);return
        start=time.monotonic();result=wait_future(h.get_result_async(),self.timeout)
        self.metrics['execution_seconds']=round(time.monotonic()-start,2)
        if result.status!=4:raise AssertionError('completed search must SUCCEED(4); got '+str(result.status))
        rr=result.result
        if gift is None:
            if rr.target_found:raise AssertionError('false positive on an empty search area')
        else:
            if not rr.target_found:raise AssertionError('target not found')
            x=float(rr.target_x);y=float(rr.target_y)
            error=math.hypot(x-(gift.x0+gift.x1)/2,y-(gift.y0+gift.y1)/2)
            self.metrics['position_error_m']=round(error,6)
            if not math.isfinite(error) or error>.05:raise AssertionError('centre error > 0.05 m')
        # Do not require a zero *after* the response; correct servers stop just before it.
        self.assert_stopped(time.monotonic()-.5)
        if not self.feedback:raise AssertionError('missing feedback')

def kill_group(p):
    if p is None:return
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait(timeout=2)

def main(args=None):
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['all','all-regression']+list(CASE_POINTS),default='all')
    p.add_argument('--namespace',default='/audit_'+str(os.getpid()));p.add_argument('--seed',type=int,default=202601)
    p.add_argument('--output',default='/workspace/reports/public-tests.json');p.add_argument('--external-server',action='store_true')
    p.add_argument('--time-scale',type=float,default=2.);p.add_argument('--timeout',type=float,default=95.)
    a=p.parse_args(args)
    names=list(CORE_WEIGHTS) if a.case=='all' else (list(REGRESSION_CASES) if a.case=='all-regression' else [a.case])
    if a.external_server and len(names)!=1:p.error('official mode uses a fresh student container for each case')
    records=[]
    for number,name in enumerate(names):
        child=None;node=None;sim=None;executor=None;thread=None;spin_stop=None;spin_errors=[]
        namespace=a.namespace if a.external_server else a.namespace+'_'+str(number)
        points=CASE_POINTS[name]
        start=time.monotonic();record={'id':name,'max_points':points,'points':0,'status':'fail','metrics':{}}
        try:
            rclpy.init();sim=Simulator(namespace,time_scale=a.time_scale,web=False);node=Audit(namespace,sim,a.timeout)
            # The auditor never blocks in an executor callback; one deterministic
            # spin thread is sufficient and avoids leaking Jazzy worker-pool tasks
            # across the independently initialized cases in a full local run.
            executor=SingleThreadedExecutor();executor.add_node(sim);executor.add_node(node)
            spin_stop=threading.Event()
            def spin_observer():
                try:
                    while not spin_stop.is_set() and rclpy.ok():
                        executor.spin_once(timeout_sec=.05)
                except Exception as exc:
                    spin_errors.append(exc);spin_stop.set()
            thread=threading.Thread(target=spin_observer,name='course-audit-spin',daemon=False);thread.start()
            if not a.external_server:
                child=subprocess.Popen(['ros2','run','hidden_gift','server','--ros-args','-r','__ns:='+namespace],start_new_session=True,
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            node.run(name,a.seed+number)
            if spin_errors:raise RuntimeError('auditor spin failed: '+str(spin_errors[0]))
            record.update(points=points,status='pass')
        except Exception as e:
            record['message']=str(e)
        finally:
            if node is not None:record['metrics']=node.metrics
            if spin_stop is not None:spin_stop.set()
            if executor is not None:executor.wake()
            if thread is not None:
                thread.join(2.)
                if thread.is_alive():
                    record.update(points=0,status='fail',message='auditor spin thread did not stop')
                elif spin_errors:
                    record.update(points=0,status='fail',message='auditor spin failed: '+str(spin_errors[0]))
            kill_group(child)
            if executor is not None and node is not None:executor.remove_node(node)
            if executor is not None and sim is not None:executor.remove_node(sim)
            if node is not None:node.destroy_node()
            if sim is not None:sim.destroy_node()
            if executor is not None:executor.shutdown(timeout_sec=2.)
            if rclpy.ok():rclpy.shutdown()
        record['wall_seconds']=round(time.monotonic()-start,2);records.append(record)
        print(json.dumps(record),flush=True)
    report={'schema':1,'lesson':'L01','authority':'external-observer' if a.external_server else 'local-formative',
        'release':os.getenv('COURSE_RELEASE','development'),'tests':records,
        'points':sum(x['points'] for x in records),'max_points':sum(x['max_points'] for x in records)}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2))
    return 0 if all(x['status']=='pass' for x in records) else 1
if __name__=='__main__':raise SystemExit(main())
