#!/usr/bin/env python3

import rospy, math
from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped
from ackermann_msgs.msg import AckermannDrive

currentState = 0
lastSteering = 0
lastV = 0
steering = 0
power = 0
backwardCount = 0


# state -1 corresponds to the backward motion
# state 0 corresponds to the break
# state 1 corresponds to the forward motion

def stateUpdate(v, w):
    # (1, v+) -> (1)
    # (1, v-) -> (0)
    # (1, 0) -> (0)
    # (0, v+) -> (1)
    # (0, v-) -> (-1)
    # (0, 0) -> (0)
    # (-1, v+) -> (1)
    # (-1, v-) -> (-1)
    # (-1, 0) -> (0)

    # It is from parameter server
    global wheelbase
    global gazeboSimulation

    # it is for describe curent state of system
    global currentState
    global lastSteering
    global lastV
    global backwardCount
    global steering
    global power

    delay = 0.1

    if (v > 0):
        # (1, v+) -> (1)
        # (0, v+) -> (1)
        # (-1, v+) -> (1)

        if (currentState == 1 or currentState == 0 or currentState == -1):
            currentState = 1
            steering = convert_trans_rot_vel_to_steering_angle(v, w, wheelbase)
            power = convert_speed_to_persantage(v)

    if (v < 0):
        # (1, v-) -> (0)
        # (0, v-) -> (-1)
        # (-1, v-) -> (-1)

        if (currentState == 1):
            power = -0.9

            if (gazeboSimulation == True):
                power = 0

            currentState = 0
            steering = lastSteering
            publishAckermannMsg(power, steering)
            rospy.sleep(delay)
            publishAckermannMsg(0, steering)
            rospy.sleep(delay)

        if (currentState == 0 or currentState == -1):
            currentState = -1

            power = convert_speed_to_persantage(v)
            steering = convert_trans_rot_vel_to_steering_angle(v, w, wheelbase)

    if (v == 0):
        # (1, 0) -> (0)
        # (0, 0) -> (0)
        # (-1, 0) -> (0)
        previousState = currentState

        if (previousState == 1):

            power = -0.3

            if (gazeboSimulation == True):
                power = 0

            publishAckermannMsg(power, 0)
            rospy.sleep(delay)

        currentState = 0
        power = 0
        steering = 0

    lastSteering = steering
    lastV = v

    publishAckermannMsg(power, steering)


def publishAckermannMsg(power, steering):
    global currentState

    rospy.loginfo("Info: power: %s, steering: %s, State: %s", power, steering, currentState)

    msg = AckermannDrive()
    # msg.header.stamp = rospy.Time.now()
    # msg.header.frame_id = frame_id
    msg.steering_angle = steering
    msg.speed = power
    pub.publish(msg)


def convert_trans_rot_vel_to_steering_angle(v, omega, wheelbase):
    if omega == 0 or v == 0:
        return 0

    radius = v / omega
    alpha = math.atan(wheelbase / radius)

    steering = convert_alpha_to_persantage(alpha)

    return steering


def convert_alpha_to_persantage(alpha):
    # mapping angel to %
    # f(-1) = pi/6
    # f(1) = pi/6
    if abs(alpha > 0.145 * math.pi ):
        rospy.loginfo("Info: Out of range. Planner error. alpha: %s. It is more that 0.45", alpha)

    # rospy.loginfo("Info: Alpha: %s.", alpha)
    return (-1) *  1 / (0.145 * math.pi) * alpha


def convert_speed_to_persantage(speed):
    # At this point we don have feedback from sensors
    # We shoould to find some constants to compensate resistatnce of the system
    # and map velocity to power of engine
    global gazeboSimulation

    if (gazeboSimulation):
        return speed

    global currentState



    forwardVelocityOffset = 0.13
    backwarddVelocityOffset = -0.36

    if (currentState == 1):
        return 0.064552 * speed + forwardVelocityOffset

    if (currentState == -1):
        return speed * 0.3 + backwarddVelocityOffset

    return 0


def cmd_callback(data):
    global ackermann_cmd_topic
    global frame_id
    global pub

    v = data.linear.x
    w = data.angular.z

    stateUpdate(v, w)


if __name__ == '__main__':
    try:

        rospy.init_node('cmd_vel_to_ackermann_drive')

        twist_cmd_topic = rospy.get_param('~twist_cmd_topic', '/cmd_vel')
        ackermann_cmd_topic = rospy.get_param('~ackermann_cmd_topic', '/drive_cmd')
        wheelbase = rospy.get_param('~wheelbase', 0.325)
        gazeboSimulation = rospy.get_param('~gazeboSimulation', False)
        frame_id = rospy.get_param('~frame_id', 'base_link')

        rospy.Subscriber(twist_cmd_topic, Twist, cmd_callback, queue_size=1)
        pub = rospy.Publisher(ackermann_cmd_topic, AckermannDrive, queue_size=1)

        rospy.loginfo(
            "Node 'cmd_vel_to_ackermann_drive' started.\nListening to %s, publishing to %s. Frame id: %s, wheelbase: %f, GazeboSim: %s",
            "/cmd_vel", ackermann_cmd_topic, frame_id, wheelbase, gazeboSimulation)

        rospy.spin()

    except rospy.ROSInterruptException:
        pass
