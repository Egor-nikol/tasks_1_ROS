#!/usr/bin/env python3
"""Inside-container course CLI. Host ./course wrapper supplies host Docker checks."""
import argparse,json,os,platform,shutil,signal,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(os.getenv('COURSE_WORKSPACE','/workspace'))

def execute_overlay(module_args):
    setup=ROOT/'install/setup.bash'
    if not setup.exists():raise RuntimeError('Run course build first')
    command=['bash','-c','source /opt/ros/jazzy/setup.bash && source /opt/course_ws/install/setup.bash && source "$1" && shift && exec "$@"','course',str(setup)]+module_args
    return subprocess.call(command,cwd=ROOT)

def doctor():
    checks=[]
    def add(name,status,detail):checks.append({'check':name,'status':status,'detail':detail})
    free=shutil.disk_usage(ROOT).free/1024**3
    add('workspace_disk','pass' if free>=3 else 'fail',f'{free:.1f} GiB free visible inside container; 30 GiB host recommendation includes images/cache')
    try:
        import rclpy
        from shad_interfaces.action import ExploreZone
        add('ros_interfaces','pass','rclpy and generated ExploreZone import')
    except Exception as e:add('ros_interfaces','fail',str(e))
    add('workspace_write','pass' if os.access(ROOT,os.W_OK) else 'fail',str(ROOT))
    for port in (8080,8081):
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=2):pass
            add('internal_port_'+str(port),'pass','listener reachable')
        except OSError as e:add('internal_port_'+str(port),'fail',str(e))
    host=os.getenv('COURSE_HOST_DOCKER')
    add('host_docker','pass' if host else 'not_checked',host or 'Inside container cannot inspect host Docker. Run ./course doctor on HOST. No socket mounting.')
    smoke=subprocess.run([sys.executable,'-m','course_lab.smoke'],capture_output=True,text=True,timeout=20)
    add('headless_smoke','pass' if smoke.returncode==0 else 'fail',(smoke.stdout+smoke.stderr)[-2500:])
    report={'schema':1,'release':os.getenv('COURSE_RELEASE'),'image_ref':os.getenv('COURSE_IMAGE_REF'),
        'architecture':platform.machine(),'python':platform.python_version(),'checks':checks,
        'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'privacy':'No hostname, user name, SSH keys, environment dump, or access token collected.'}
    dest=ROOT/'reports/environment.json';dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2));print('Report:',dest)
    return 1 if any(x['status']=='fail' for x in checks) else 0

def dev():
    home=Path(os.environ['HOME']);home.mkdir(parents=True,exist_ok=True)
    (home/'.bashrc').write_text('source /opt/ros/jazzy/setup.bash\nsource /opt/course_ws/install/setup.bash\ncd /workspace\n')
    processes=[]
    try:
        processes.append(subprocess.Popen(['ros2','run','course_lab','simulator'],start_new_session=True))
        processes.append(subprocess.Popen(['code-server','--bind-addr','0.0.0.0:8080','--auth','none','--disable-telemetry',str(ROOT)],start_new_session=True))
        while all(p.poll() is None for p in processes):time.sleep(.5)
        return 1
    finally:
        for p in processes:
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
        for p in processes:
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass

def main():
    args=sys.argv[1:]
    if not args:print('course doctor | smoke | build | run | goal | test | demo | dev');return 0
    cmd,rest=args[0],args[1:]
    if cmd=='doctor':return doctor()
    if cmd=='smoke':return subprocess.call([sys.executable,'-m','course_lab.smoke'])
    if cmd=='build':
        # Infrastructure/interface packages are pre-built in the immutable underlay.
        return subprocess.call(['colcon','build','--base-paths','src/hidden_gift','--symlink-install'],cwd=ROOT)
    if cmd=='run':return execute_overlay(['ros2','run','hidden_gift','server','--ros-args','-r','__ns:=/lab']+rest)
    if cmd=='goal':return subprocess.call([sys.executable,'-m','course_lab.client']+rest)
    if cmd=='test':return execute_overlay([sys.executable,'-m','course_lab.audit']+rest)
    if cmd=='demo':
        name=rest.pop(0) if rest else 'executor'
        if name=='executor':return subprocess.call(['ros2','run','course_lab','concurrency_demo']+rest)
        if name=='deadlock':return subprocess.call(['timeout','--kill-after=2s','6s',sys.executable,'-m','course_lab.deadlock_demo']+rest)
        raise ValueError('Unknown demo')
    if cmd=='dev':return dev()
    raise ValueError('Unknown command: '+cmd)
if __name__=='__main__':
    try:raise SystemExit(main())
    except KeyboardInterrupt:raise SystemExit(130)
    except Exception as e:print('ERROR:',e,file=sys.stderr);raise SystemExit(2)
