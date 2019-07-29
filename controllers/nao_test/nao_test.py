"""nao_test controller."""
from controller import Robot, Motion
from time import sleep
import os

# create the Robot instance.
robot = Robot()

print(os.getcwd())
# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())
# get motion file
handWave = Motion('../../motions/sample.motion')
handWave.setLoop(True)
# Main loop:
# nao move by using motion file
while robot.step(timestep) != -1:
    handWave.play()
