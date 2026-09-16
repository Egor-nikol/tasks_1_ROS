"""Supplied helpers: geometry is not the main learning goal of lesson 01."""
import math
from .world import Area, Sample

def drive_to(p: Sample, target: tuple[float,float], speed=1.7, tolerance=0.025):
    dx=target[0]-p.x; dy=target[1]-p.y
    distance=math.hypot(dx,dy)
    if distance<=tolerance: return 0.0,0.0,True
    err=math.atan2(math.sin(math.atan2(dy,dx)-p.theta),math.cos(math.atan2(dy,dx)-p.theta))
    angular=max(-3.,min(3.,5.*err))
    linear=min(speed,2.5*distance) if abs(err)<0.18 else 0.0
    return linear,angular,False

def raster(a: Area, spacing=0.45):
    if not a.valid() or spacing<=0 or not math.isfinite(spacing):
        raise ValueError('invalid area or spacing')
    n=max(1,math.ceil((a.y1-a.y0)/spacing))
    result=[]
    for i in range(n):
        y=a.y0+(i+0.5)*(a.y1-a.y0)/n
        margin=min(.02,(a.x1-a.x0)/4)
        ends=(a.x0+margin,a.x1-margin) if i%2==0 else (a.x1-margin,a.x0+margin)
        for x in ends: result.append((x,y))
    return result
