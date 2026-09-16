"""STUDENT FILE. Implement the search state machine. No ROS calls in this module.
Use raster() and drive_to(); never read simulator internals or web /state.
Return Outcome('absent') ONLY after covering the entire requested area.
Return Outcome('found', x, y) after measuring the rectangle centre.
"""
from course_lab.world import Area, Sample, Decision
from course_lab.navigation import drive_to, raster
from course_lab.probe import RectangleProbe

class Mission:
    def __init__(self, area: Area):
        self.area = area
        self.waypoints = raster(area)
        self.index = 0

    def step(self, sample: Sample) -> Decision:
        # TODO M1: follow raster; on green INSIDE area instantiate RectangleProbe.
        # Probe already measures boundaries. Delegate future samples to probe.step().
        # Basic feedback and all safety/failure policy are supplied by the adapter.
        # Starter is intentionally stopped, not a working submission.
        return Decision()
