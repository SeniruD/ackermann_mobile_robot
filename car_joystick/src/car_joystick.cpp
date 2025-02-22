#include "ros/ros.h"
#include "std_msgs/String.h"
#include "ackermann_msgs/AckermannDrive.h"
#include <sensor_msgs/Joy.h>

ros::Publisher chatter_pub;

void chatterCallback(const sensor_msgs::Joy::ConstPtr& msg) {
    ackermann_msgs::AckermannDrive out;
    out.steering_angle = msg->axes[2]*-1;
    ROS_INFO("Angle: %f", out.steering_angle);
    out.speed = msg->axes[1];
	
	//for slown driving	
//    if (out.speed > 0.12) {
  //	   out.speed = 0.12;
   // }

    ROS_INFO("Speed: %f", out.speed);
    chatter_pub.publish(out);
    ros::spinOnce();
}

int main(int argc, char **argv)
{
    ros::init(argc, argv, "ackermann_joy");

    ros::NodeHandle n;
    chatter_pub = n.advertise<ackermann_msgs::AckermannDrive>("drivecmd", 100);
    ros::Rate loop_rate(5);
    ros::Subscriber sub = n.subscribe("joy", 1000, chatterCallback);
    ros::spin();
    return 0;
}
