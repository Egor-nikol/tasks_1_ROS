"""Supplied geometry helper. Students focus on ROS contracts, not boundary-search code.
Call RectangleProbe(area, first_green_sample), then .step(sample) every tick.
Returned Decision.outcome is found or abort; propagate cancellation in your ROS adapter.
The point robot / axis-aligned rectangle / noiseless sensor assumptions are essential.
"""
import math
from .world import Decision, Outcome
from .navigation import drive_to

class RectangleProbe:
    def __init__(self,area,seed):
        if not seed.green or not area.contains(seed.x,seed.y):
            raise ValueError('Need a green sample inside the search area')
        self.area=area; self.seed=(seed.x,seed.y)
        self.edge={};self.last=None;self.last_green=None;self.distance=0.;self.detected=True
        self.target=None;self.cx=0.;self.phase='interior';self.candidate=0;self.probe_index=0
        self.candidates=[(seed.x+dx,seed.y+dy) for dx,dy in
          [(0.,0.),(.25,.25),(.25,-.25),(-.25,.25),(-.25,-.25),(.25,0.),(-.25,0.),(0.,.25),(0.,-.25)]]
        self.candidates=[(x,y) for x,y in self.candidates if area.contains(x,y)]

    def finish(self,kind,x=0.,y=0.):
        return Decision(outcome=Outcome(kind,x,y),detected=self.detected,distance=self.distance)

    def step(self,s):
        fresh=self.last is None or s.sequence!=self.last.sequence
        if fresh and self.last is not None:
            self.distance+=math.hypot(s.x-self.last.x,s.y-self.last.y)
        if fresh: self.last=s
        a=self.area
        if self.phase=='interior':
            if self.candidate>=len(self.candidates):
                return self.finish('abort')  # model contract violated or navigation error
            x,y=self.candidates[self.candidate]
            pts=[(x-.10,y),(x+.10,y),(x,y-.10),(x,y+.10),(x,y)]
            target=pts[self.probe_index]
            if not a.contains(*target):
                self.candidate+=1; self.probe_index=0
                return Decision(detected=True,distance=self.distance)
            v,w,done=drive_to(s,target,speed=1.0,tolerance=.012)
            if done and fresh:
                if s.green:
                    self.probe_index+=1
                    if self.probe_index==len(pts):
                        self.seed=(s.x,s.y); self.last_green=s
                        self.phase='left'; self.target=(a.x0,s.y)
                else:
                    self.candidate+=1; self.probe_index=0
                return Decision(detected=True,distance=self.distance)
            return Decision(v,w,detected=True,distance=self.distance)
        if self.phase=='center_x':
            v,w,done=drive_to(s,self.target,speed=1.)
            if done:
                self.phase='bottom'; self.last_green=s; self.target=(self.cx,a.y0)
                return Decision(detected=self.detected,distance=self.distance)
            return Decision(v,w,detected=self.detected,distance=self.distance)
        axis=0 if self.phase in ('left','right') else 1
        coord=s.x if axis==0 else s.y
        bound={'left':a.x0,'right':a.x1,'bottom':a.y0,'top':a.y1}[self.phase]
        crossed=False
        if fresh and s.green:
            self.last_green=s
        if fresh and not s.green and self.last_green is not None:
            old=self.last_green.x if axis==0 else self.last_green.y
            self.edge[self.phase]=(coord+old)/2.
            crossed=True
        # A gift can touch the world/search boundary; don't wait to leave the world.
        if s.green and abs(coord-bound)<0.035:
            self.edge[self.phase]=bound; crossed=True
        if crossed:
            phase=self.phase
            if phase=='left':
                self.phase='right'; self.target=(a.x1,self.seed[1]); self.last_green=None
            elif phase=='right':
                self.cx=(self.edge['left']+self.edge['right'])/2.
                self.phase='center_x'; self.target=(self.cx,self.seed[1]); self.last_green=None
            elif phase=='bottom':
                self.phase='top'; self.target=(self.cx,a.y1); self.last_green=None
            else:
                cy=(self.edge['bottom']+self.edge['top'])/2.
                return self.finish('found',self.cx,cy)
            return Decision(detected=True,distance=self.distance)
        v,w,_=drive_to(s,self.target,speed=1.,tolerance=0.015)
        return Decision(v,w,detected=self.detected,distance=self.distance)
