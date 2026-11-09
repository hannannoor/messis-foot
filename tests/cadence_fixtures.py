"""Synthetic observation fixtures; no match assets."""
from gap_solver.motion import motion_frame


def moving_fixture(count=180, stride=1):
    frames=[]
    for i in range(count):
        bx=25+.08*i
        available=i%stride==0
        frames.append(motion_frame(1,(bx,34) if available else None,
            [(bx+1,34),(10,10),(15,15)],[(bx+10,34),(70,55),(75,60)],
            ball_native_observation=available,ball_sample_time_s=i/25 if available else None))
    return frames
