#!/usr/bin/env python

import os
import math
import time
import rospy
import numpy as np
import tf
from find_object_2d.msg import DetectionInfo
from visualization_msgs.msg import Marker, MarkerArray
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge


class Objects:
    ALIVE = "alive"
    BIOHAZARD = "biohazard"
    DANGER = "danger"
    DEAD = "dead"
    FLAMABLE = "flamable"
    NOSMOKING = "nosmoking"
    RADIOACTIVE = "radioactive"
    REDTRIANGLE = "redtriangle"
    TOXIC = "toxic"

    def __init__(self):
        self.obj_dict = {}

    def add_object_to_dict(self, object_name, position):
        if not(object_name in self.obj_dict.keys()):
            self.obj_dict[object_name] = [position]
        else:
            for index, item in enumerate(self.obj_dict[object_name]):
                pos_diff = ((item[0]-position[0])**2) + \
                    ((item[1]-position[1])**2)+((item[2]-position[2])**2)
                pos_diff = math.sqrt(pos_diff)
                if pos_diff > 3:
                    self.obj_dict[object_name].append(position)
                else:
                    self.obj_dict[object_name][index] = position


class ObjectRecognition:
    def __init__(self):
        self.tf_listener = tf.TransformListener()
        self.objects = Objects()
        self.pub_markers = rospy.Publisher(
            '/marker_array', MarkerArray, queue_size=1)
        self.sub_rgb_img = rospy.Subscriber(
            '/camera/rgb/image_raw', Image, self.image_callback)
        self.sub_detect_info = rospy.Subscriber(
            '/info', DetectionInfo, self.find_object_callback)

    def image_callback(self, msg: Image):
        try:
            cv_bridge = CvBridge()
            cv_image = cv_bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        except Exception as e:
            rospy.logwarn(e)

    def is_red_present(self):
        red_lower = np.array([0, 50, 50])
        red_upper = np.array([10, 255, 255])
        mask0 = cv2.inRange(self.hsv_image, red_lower, red_lower)
        red_lower = np.array([170, 50, 50])
        red_lower = np.array([180, 255, 255])
        mask1 = cv2.inRange(self.hsv_image, red_lower, red_lower)
        mask = mask0 + mask1
        return np.count_nonzero(mask) > 10

    def is_green_present(self):
        green_lower = np.array([40, 50, 50])
        green_upper = np.array([85, 255, 255])
        mask = cv2.inRange(self.hsv_image, green_lower, green_upper)
        return np.count_nonzero(mask) > 10

    def find_object_callback(self, msg: DetectionInfo):
        target_frame = 'map'
        for file_index, file_path in enumerate(msg.filePaths):
            file_path = file_path.data
            object_name = os.path.splitext(os.path.basename(file_path))[0]
            object_frame = 'object_' + str(msg.ids[file_index].data)

            if ((object_name == Objects.ALIVE) or (object_name == Objects.DEAD)):
                if self.is_red_present():
                    object_name = Objects.DEAD
                elif self.is_green_present():
                    object_name = Objects.ALIVE

            try:
                self.tf_listener.waitForTransform(
                    target_frame, object_frame, rospy.Time(0), rospy.Duration(2))
                pos, quat = self.tf_listener.lookupTransform(
                    target_frame, object_frame, rospy.Time(0))
                self.objects.add_object_to_dict(object_name, pos)
                print(self.objects.obj_dict)
            except Exception as e:
                rospy.logwarn(e)

        mrk_arr = MarkerArray()
        for key in self.objects.obj_dict:
            obj = self.objects.obj_dict[key]
            for __, pos in enumerate(obj):
                marker = Marker()
                marker.header.frame_id = 'map'
                marker.header.stamp = rospy.Time()
                marker.ns = key
                marker.id = 0
                marker.type = marker.CUBE
                marker.action = marker.ADD
                marker.pose.position.x = pos[0]
                marker.pose.position.y = pos[1]
                marker.pose.position.z = pos[2]
                marker.pose.orientation.x = 0.0
                marker.pose.orientation.y = 0.0
                marker.pose.orientation.z = 0.0
                marker.pose.orientation.w = 1.0
                marker.scale.x = 0.5
                marker.scale.y = 0.5
                marker.scale.z = 0.5
                marker.color.a = 1.0
                if key == Objects.ALIVE:
                    marker.color.r = 0.0
                    marker.color.g = 1.0
                    marker.color.b = 0.0
                elif key == Objects.DEAD:
                    marker.color.r = 1.0
                    marker.color.g = 0.0
                    marker.color.b = 0.0
                else:
                    marker.color.r = 0.5
                    marker.color.g = 0.5
                    marker.color.b = 0.5
                mrk_arr.markers.append(marker)

        self.pub_markers.publish(mrk_arr)

    def main(self):
        rospy.spin()


if __name__ == "__main__":
    rospy.init_node('object_detect_node')
    obj_rec = ObjectRecognition()
    obj_rec.main()
