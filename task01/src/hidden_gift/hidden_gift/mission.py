"""STUDENT FILE. Implement the search state machine. No ROS calls in this module.
Use raster() and drive_to(); never read simulator internals or web /state.
Return Outcome('absent') ONLY after covering the entire requested area.
Return Outcome('found', x, y) after measuring the rectangle centre.
"""
from math import hypot
from course_lab.world import Area, Sample, Decision, Outcome
from course_lab.navigation import drive_to, raster
from course_lab.probe import RectangleProbe

class Mission:
    def __init__(self, area: Area):
        self.area = area
        self.waypoints = raster(area)
        self.index = 0

        self.found_green = False
        self.probe = None
        self.previous = None
        self.distance = 0.0

    def step(self, sample: Sample) -> Decision:
        if self.previous is not None:
            dx = sample.x - self.previous.x
            dy = sample.y - self.previous.y
            self.distance += hypot(dx, dy)

        self.previous = sample
        if not self.found_green:
            if sample.green and self.area.contains(sample.x, sample.y):
                self.found_green = True
                self.probe = RectangleProbe(self.area, sample)

        if self.found_green:
            decision = self.probe.step(sample)

            return Decision(v=decision.v, w=decision.w,
                outcome=decision.outcome,
                detected=True,
                distance=self.distance
            )

        if self.index >= len(self.waypoints) and not self.found_green:
            return Decision(outcome=Outcome("absent"), distance=self.distance)
        point = self.waypoints[self.index]
        v, w, reached = drive_to(sample, point)
        if reached:
            self.index += 1

        return Decision(v=v, w=w, distance=self.distance)