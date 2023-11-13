#! /usr/bin/env python3
from __future__ import print_function
import importlib
import rospy
import actionlib
from control_msgs.msg import FollowJointTrajectoryAction
from control_msgs.msg import FollowJointTrajectoryFeedback
from control_msgs.msg import FollowJointTrajectoryResult
import stretch_body.robot as rb
import time
import numpy as np
class JointTrajectoryAction:

    def __init__(self, node, robot):
        self.node = node
        self.robot : rb.Robot = robot
        self.server = actionlib.SimpleActionServer('/alfred_controller/follow_joint_trajectory',
                                                   FollowJointTrajectoryAction,
                                                   execute_cb=self.execute_cb,
                                                   auto_start=False)
        self.feedback = FollowJointTrajectoryFeedback()
        self.result = FollowJointTrajectoryResult()

    def execute_cb(self, goal):
        
        with self.node.robot_stop_lock:
            self.node.stop_the_robot = False
        # self.node.robot_mode_rwlock.acquire_read()

        for i, name in enumerate(goal.trajectory.joint_names):
            joint, motionType = name.split(';')
            pos = goal.trajectory.points[0].positions[i]
            rospy.loginfo("joint: {0}, motionType: {1}, by {2}".format(joint, motionType, pos))
            if 'head' in joint:
                if motionType == 'to':
                    self.robot.head.move_to(joint, pos)
                else:
                    self.robot.head.move_by(joint, pos)
            elif 'base_translate' in joint:
                if motionType == 'vel':
                    self.robot.base.set_translate_velocity(pos)
                elif motionType == 'by':
                    self.robot.base.translate_by(pos)
            elif 'base_rotate' in joint:
                if motionType == 'vel':
                    self.robot.base.set_rotational_velocity(pos)
                elif motionType == 'by':
                    self.robot.base.rotate_by(pos)
            elif 'lift' in joint:
                if motionType == 'to':
                    self.robot.lift.move_to(pos)
                elif motionType == 'vel':
                    self.robot.lift.set_velocity(pos)
                elif motionType == 'by':
                    self.robot.lift.move_by(pos)
            elif 'arm' in joint:
                if motionType == 'to':
                    self.robot.arm.move_to(pos)
                elif motionType == 'vel':
                    self.robot.arm.set_velocity(pos)
                elif motionType == 'by':
                    self.robot.arm.move_by(pos)
            elif 'stretch_gripper' in joint:
                if motionType == 'to':
                    self.robot.end_of_arm.move_to("stretch_gripper", pos) 
            elif 'wrist_yaw' in joint:
                if motionType == 'to':
                    self.robot.end_of_arm.move_to("wrist_yaw", pos * np.pi/180)  
        self.robot.push_command()
        
        rospy.loginfo("Waiting for arm to stop moving")
        self.robot.arm.wait_until_at_setpoint()
        rospy.loginfo("Waiting for lift to stop moving")
        self.robot.lift.wait_until_at_setpoint()
        
        # rospy.loginfo("Waiting for base to stop moving")
        # self.robot.base.wait_until_at_setpoint()
        while self.robot.head.motors['head_pan'].motor.is_moving():
            rospy.loginfo("head_pan is still moving")
            time.sleep(0.1)
        while self.robot.head.motors['head_tilt'].motor.is_moving():
            rospy.loginfo("head_tilt is still moving")
            time.sleep(0.1)
            
        while self.robot.end_of_arm.motors['wrist_yaw'].motor.is_moving():
            rospy.loginfo("wrist_yaw is still moving")
            time.sleep(0.1)
        while self.robot.end_of_arm.motors['stretch_gripper'].motor.is_moving():
            rospy.loginfo("stretch_gripper is still moving")
            time.sleep(0.1)
            
        rospy.loginfo("Complete")
        self.success_callback("set command.")
        # self.robot_mode_rwlock.release_read()
        

    def invalid_joints_callback(self, err_str):
        if self.server.is_active() or self.server.is_preempt_requested():
            rospy.logerr("{0} joint_traj action: {1}".format(self.node.node_name, err_str))
            self.result.error_code = self.result.INVALID_JOINTS
            self.result.error_string = err_str
            self.server.set_aborted(self.result)

    def invalid_goal_callback(self, err_str):
        if self.server.is_active() or self.server.is_preempt_requested():
            rospy.logerr("{0} joint_traj action: {1}".format(self.node.node_name, err_str))
            self.result.error_code = self.result.INVALID_GOAL
            self.result.error_string = err_str
            self.server.set_aborted(self.result)

    def goal_tolerance_violated_callback(self, err_str):
        if self.server.is_active() or self.server.is_preempt_requested():
            rospy.logerr("{0} joint_traj action: {1}".format(self.node.node_name, err_str))
            self.result.error_code = self.result.GOAL_TOLERANCE_VIOLATED
            self.result.error_string = err_str
            self.server.set_aborted(self.result)

    def success_callback(self, success_str):
        # rospy.loginfo("{0} joint_traj action: {1}".format(self.node.node_name, success_str))
        self.result.error_code = self.result.SUCCESSFUL
        self.result.error_string = success_str
        self.server.set_succeeded(self.result)
