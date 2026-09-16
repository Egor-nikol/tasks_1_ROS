"""ROS-free, fixed-step unicycle world. No teleport/reset ROS service is exposed."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Area:
    x0: float
    y0: float
    x1: float
    y1: float
    def contains(self, x, y):
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1
    def valid(self):
        return all(math.isfinite(v) for v in (self.x0,self.y0,self.x1,self.y1)) and 0 <= self.x0 < self.x1 <= 11 and 0 <= self.y0 < self.y1 <= 11

@dataclass(frozen=True)
class Sample:
    x: float
    y: float
    theta: float
    green: bool
    sequence: int
    received: float

@dataclass(frozen=True)
class Outcome:
    kind: str  # found | absent | canceled | abort
    x: float = 0.0
    y: float = 0.0
    reason: str = ''

@dataclass(frozen=True)
class Decision:
    v: float = 0.0
    w: float = 0.0
    outcome: Outcome | None = None
    detected: bool = False
    distance: float = 0.0

class World:
    SIZE = 11.0
    MAX_V = 2.0
    MAX_W = 3.0
    def __init__(self, pose=(1.0,1.0,0.0), gift=None):
        self.x,self.y,self.theta = map(float,pose)
        self.gift = gift
        self.v=self.w=0.0
        self.sequence=0
        self.distance=0.0
        self.sim_time=0.0
        self.invalid_commands=0
        self.limit_violations=0
    def command(self, v, w):
        if not math.isfinite(v) or not math.isfinite(w):
            self.invalid_commands+=1; self.v=self.w=0.0; return
        if abs(v)>self.MAX_V+1e-6 or abs(w)>self.MAX_W+1e-6:
            self.limit_violations+=1
        self.v=max(-self.MAX_V,min(self.MAX_V,v))
        self.w=max(-self.MAX_W,min(self.MAX_W,w))
    def step(self, dt):
        if not math.isfinite(dt) or dt<=0 or dt>0.1:
            raise ValueError('dt must be in (0, 0.1]')
        t=self.theta; a=t+self.w*dt
        if abs(self.w)<1e-9:
            dx=self.v*math.cos(t)*dt; dy=self.v*math.sin(t)*dt
        else:
            dx=self.v/self.w*(math.sin(a)-math.sin(t))
            dy=self.v/self.w*(-math.cos(a)+math.cos(t))
        nx=max(0.,min(self.SIZE,self.x+dx)); ny=max(0.,min(self.SIZE,self.y+dy))
        self.distance+=math.hypot(nx-self.x,ny-self.y)
        self.x,self.y=nx,ny
        self.theta=math.atan2(math.sin(a),math.cos(a))
        self.sequence+=1; self.sim_time+=dt
    def sample(self, now):
        green=self.gift is not None and self.gift.contains(self.x,self.y)
        return Sample(self.x,self.y,self.theta,green,self.sequence,now)
