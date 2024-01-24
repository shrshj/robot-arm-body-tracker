#!/usr/bin/env python3

import sys
import math
import time
import queue
import datetime
import random
import traceback
import threading
from xarm import version
from xarm.wrapper import XArmAPI
import socket
import math



class RobotMain(object):
    """Robot Main Class"""
    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._tcp_speed = 100
        self._tcp_acc = 20
        self._angle_speed = 20
        self._angle_acc = 5
        self._vars = {}
        self._funcs = {}
        self._robot_init()

    # Robot init
    def _robot_init(self):
        self._arm.clean_warn()
        self._arm.clean_error()
        self._arm.motion_enable(True)
        self._arm.set_mode(0)
        self._arm.set_state(0)
        time.sleep(1)
        self._arm.register_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.register_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, 'register_count_changed_callback'):
            self._arm.register_count_changed_callback(self._count_changed_callback)

    # Register error/warn changed callback
    def _error_warn_changed_callback(self, data):
        if data and data['error_code'] != 0:
            self.alive = False
            self.pprint('err={}, quit'.format(data['error_code']))
            self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)

    # Register state changed callback
    def _state_changed_callback(self, data):
        if data and data['state'] == 4:
            self.alive = False
            self.pprint('state=4, quit')
            self._arm.release_state_changed_callback(self._state_changed_callback)

    # Register count changed callback
    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint('counter val: {}'.format(data['count']))

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint('{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}'.format(label, code, self._arm.connected, self._arm.state, self._arm.error_code, ret1, ret2))
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print('[{}][{}] {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), stack_tuple[1], ' '.join(map(str, args))))
        except:
            print(*args, **kwargs)

    @property
    def arm(self):
        return self._arm

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._arm.connected and self._arm.error_code == 0:
            if self._arm.state == 5:
                cnt = 0
                while self._arm.state == 5 and cnt < 5:
                    cnt += 1
                    time.sleep(0.1)
            return self._arm.state < 4
        else:
            return False
        
class Track:
    def track_body(self, udp_conn):
        thread = threading.Thread(target=udp_conn.receive_data)
        thread.start() 
        
        while True:
            
            current_angle_pose = arm.get_servo_angle()[1]
            joint_1 = current_angle_pose[0]
            joint_2 = current_angle_pose[1]
            joint_3 = current_angle_pose[2]
            joint_4 = current_angle_pose[3]
            joint_5 = current_angle_pose[4]
            joint_6 = current_angle_pose[5]

            # Default value of next joint positions
            new_joint_1 = joint_1
            new_joint_2 = joint_2
            new_joint_3 = joint_3
            new_joint_4 = joint_4
            new_joint_5 = joint_5
            new_joint_6 = joint_6

            # To-Do
            # 1- Get UDP latest data
            # 2- Extract body nose position
            # 3- Do mathematic calculation (Inverse Kinematic)
            # 4- Set new joint positions and move the robot

            
            new_angle_pose = [new_joint_1, new_joint_2, new_joint_3, new_joint_4, new_joint_5, new_joint_6]
            arm.set_servo_angle(angle = new_angle_pose, speed=150, wait=True, radius=50.0)
            print("Arms : " + str(arm.get_servo_angle(is_radian=False)))
    

class UDP:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
    
    def receive_data(self):
        while True:
            # To Do
            pass
    
if __name__ == '__main__':
    
    # Robot setting
    RobotMain.pprint('xArm-Python-SDK Version:{}'.format(version.__version__))
    arm = XArmAPI('192.168.1.185', baud_checkset=False)
    robot_main = RobotMain(arm)
    arm.set_servo_angle(angle=[0, 0, 120, 0, 30, 0], speed=30, mvacc=360, wait=True, radius=50.0) # Custom defined home position
    
    
    # Udp connection
    UDP_IP = "0"
    UDP_PORT = 5052
    udp = UDP(UDP_IP, UDP_PORT)
    
    # Track
    t = Track()
    t.track_body(udp)
    