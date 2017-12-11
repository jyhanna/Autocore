class Message(object):
    identifier = "None"

class Pose(Message):
    x = 0.0
    y = 0.0
    z = 0.0

class Velocity(Message):
    dx = 0.0
    dy = 0.0
    dz = 0.0

class BinarySensor(Message):
    state = 0

class ImageStream(Message):
    resolution = (0, 0)
    data = []
