# coding:utf-8
import sys
import os
import time
import shutil
from naoqi import ALProxy
import quaternion
import transformations
import math
import glob
import threading
import texttospeech

class naoMirroring():
    def __init__(self):
        # -- nao setup --#
        IP = "163.221.124.196"
        user_name = 'nao'
        self.file_no = 60
        self.motion = ALProxy("ALMotion", IP, 9559)
        self.tracker = ALProxy("ALTracker", IP, 9559)
        self.motion.wakeUp()
        self.motion.setStiffnesses("Head", 1.0)
        self.motion.setStiffnesses("Body", 1.0)
        self.tracker.stopTracker()
        self.sound = ALProxy("ALSoundDetection", IP, 9559)
        self.speech = ALProxy("ALSpeechRecognition", IP, 9559)
        self.people = ALProxy("ALPeoplePerception", IP, 9559)
        self.face = ALProxy("ALFaceDetection", IP, 9559)
        self.autonumous = ALProxy("ALAutonomousMoves", IP, 9559)
        self.people.setFaceDetectionEnabled(False)
        self.people.setMaximumDetectionRange(0)
        self.face.setRecognitionEnabled(False)
        self.face.setTrackingEnabled(False)
        self.sound.setParameter("Sensitivity", 0.0)
        self.speech.setParameter("Sensitivity", 0.0)
        self.autonumous.setExpressiveListeningEnabled(False)

        # -- multi thread --#
        self.stop_event = threading.Event()
        self.speak_thread = threading.Thread(target = self.speaking)
        self.mirror_thread = threading.Thread(target = self.mirroring)
        self.speak_thread.start()
        self.mirror_thread.start()

    def stop(self):
        self.stop_event.set()
        # self.thread.join()

    # あらかじめ取得した人の関節座標を古い順に読み込む
    def read_file(self):
        print("now file No. " + str(self.file_no) + "\n")
        k_dic = {}
        file_loop = 0
        line_count = 0
        now_file = 'taiwasha6/' + str(self.file_no) + '.txt'
        # 動きを滑らかにするために、前2つのファイルを読み込む
        one_before_file = 'data/' + str(self.file_no - 20) + '.txt'
        two_before_file = 'data/' + str(self.file_no - 40) + '.txt'

        for file in [now_file, one_before_file, two_before_file]:
            file_loop += 1
            with open(file, 'r') as f:
                for line in f:
                    if line_count == 16:
                        break
                    k_items = line.split(",")
                    # 3つのファイルの座標をk_dicに入れて、平均をとる
                    if file_loop == 1:
                        k_dic[int(k_items[0])] = [float(k_items[1]), float(k_items[2]), float(k_items[3])]
                    else:
                        k_dic[int(k_items[0])] = [k_dic[int(k_items[0])][0] + float(k_items[1]),\
                        k_dic[int(k_items[0])][1] + float(k_items[2]), k_dic[int(k_items[0])][2] + float(k_items[3])]
                    line_count += 1
        for k, v in k_dic.items():
            k_dic[k] = [i/3 for i in v]
        self.file_no += 20
        return k_dic

    def vec_conv(self,joint_data):
        R_shoulder_elb = [joint_data[8][0]-joint_data[2][0], joint_data[8][1]-joint_data[2][1], joint_data[8][2]-joint_data[2][2]]
        R_elb_wrist = [joint_data[9][0]-joint_data[8][0], joint_data[9][1]-joint_data[8][1], joint_data[9][2]-joint_data[8][2]]
        return R_shoulder_elb, R_elb_wrist

    def angleHeadPitch(self, x2, y2, z2, x1, y1, z1):
        angle = math.atan((x2-x1)/(z2-z1))
        angle = math.degrees(angle)
        return -angle

    def angleHeadYaw(self, x2, y2, z2, x1, y1, z1):
        angle = math.atan((x2-x1)/(z2-z1))
        angle2 = math.atan((x2-x1)/(z2-z1))
        angle = math.degrees(angle)
        angle2 = math.degrees(angle2)
        print(angle, angle2)
        return -angle

    def angleRShoulderPitch(self, x2, y2, z2, x1, y1, z1): #calulates the Shoulderpitch value for the Right shoulder by using geometry
        if(y2<y1):
            angle = math.atan(abs(y2 - y1) / abs(z2 - z1))
            angle = math.degrees(angle)
            angle = -(angle)
            if(angle<-118):
                angle = -117
            return angle
        else:
            angle = math.atan((z2-z1)/(y2-y1))
            angle = math.degrees(angle)
            angle = 90-angle
            if angle < 90:
                return angle
            else:
                return 90

    def angleRShoulderRoll(self, x2, y2, z2, x1, y1, z1): #calulates the ShoulderRoll value for the Right shoulder by using geometry
        if(z2<z1):
            test = z2
            anderetest = z1
            z2=anderetest
            z1=test
        if (z2 - z1 < 0.1):
            z2 = 1.0
            z1 = 0.8
        angle = math.atan((x2 - x1) / (z2 - z1))
        angle = math.degrees(angle)
        return -angle

    def angleLShoulderPitch(self, x2, y2, z2, x1, y1, z1): #calulates the Shoulderpitch value for the Left shoulder by using geometry
        if (y2 < y1):
            angle = math.atan(abs(y2 - y1) / abs(z2 - z1))
            angle = math.degrees(angle)
            angle = -(angle)
            if (angle < -118):
                angle = -117
            return angle
        else:
            angle = math.atan((z2 - z1) / (y2 - y1))
            angle = math.degrees(angle)
            angle = 90 - angle
            # 肩関節が後ろに回らないための工夫
            if angle < 90:
                return angle
            else:
                return 90

    def angleLShoulderRoll(self, x2, y2, z2, x1, y1, z1): #calulates the ShoulderRoll value for the Left shoulder by using geometry
        if (z2 < z1):
            test = z2
            anderetest = z1
            z2 = anderetest
            z1 = test
        if(z2-z1< 0.1):
            z2=1.0
            z1=0.8
        angle = math.atan((x2-x1)/(z2-z1))
        angle = math.degrees(angle)
        return -angle

    # RelbowYawはshoulderpitch60以上で-方向に曲がらないようにする
    def angleRElbowYaw(self, x2, y2, z2, x1, y1, z1,shoulderpitch): #calulates the ElbowYaw value for the Right elbow by using geometry
        if(abs(y2-y1)<0.2 and abs(z2-z1) < 0.2 and (x1<x2) ):
            return 0
        elif(abs(x2-x1)<0.1 and abs(z2-z1)<0.1 and (y1>y2)):
            return 90
        elif(abs(x2-x1)<0.1 and abs(z2-z1)<0.1 and (shoulderpitch > 50)):
            return 90
        elif(abs(y2-y1)<0.1 and abs(z2-z1)<0.1 and (shoulderpitch < 50)):
            return 0
        elif(abs(x2-x1)<0.1 and abs(y2-y1)<0.1 and (shoulderpitch > 50)):
            return 90
        else:
            angle = math.atan((z2 - z1) / (y2 - y1))
            angle = math.degrees(angle)
            angle = - angle + (shoulderpitch)
            angle = - angle
            if angle > 0 and shoulderpitch > 60:
                return angle
            else:
                return 0


    def angleRElbowRoll(self, x3, y3, z3, x2, y2, z2, x1, y1, z1): #calulates the ElbowRoll value for the Right elbow by using geometry
        a1=(x3-x2)**2+(y3-y2)**2 + (z3-z2)**2
        lineA= a1 ** 0.5                        # calculates length of line between 2 3D coordinates
        b1=(x2-x1)**2+(y2-y1)**2 + (z2-z1)**2
        lineB= b1 ** 0.5                        # calculates length of line between 2 3D coordinates
        c1=(x1-x3)**2+(y1-y3)**2 + (z1-z3)**2
        lineC= c1 ** 0.5                        # calculates length of line between 2 3D coordinates

        cosB = (pow(lineA, 2) + pow(lineB,2) - pow(lineC,2))/(2*lineA*lineB)
        acosB = math.acos(cosB)
        angle = math.degrees(acosB)
        angle = 180 - angle
        return angle


    def angleLElbowYaw(self, x2, y2, z2, x1, y1, z1, shoulderpitch): #calulates the ElbowYaw value for the Left elbow by using geometry
        if(abs(y2-y1)<0.2 and abs(z2-z1) < 0.2 and (x1>x2) ):
            return 0
        elif(abs(x2-x1)<0.1 and abs(z2-z1)<0.1 and (y1>y2)):
            return -90
        elif(abs(x2-x1)<0.1 and abs(z2-z1)<0.1 and (shoulderpitch > 50)):
            return -90
        elif(abs(y2-y1)<0.1 and abs(z2-z1)<0.1 and (shoulderpitch > 50)):
            return 0
        elif(abs(x2-x1)<0.1 and abs(y2-y1)<0.1 and (shoulderpitch > 50)):
            return -90
        else:
            angle = math.atan((z2 - z1) / (y2 - y1))
            angle = math.degrees(angle)
            angle = - angle + (shoulderpitch)
            angle = - angle
            if angle < 0 and shoulderpitch > 60:
                return angle
            else:
                return 0

    def angleLElbowRoll(self, x3, y3, z3, x2, y2, z2, x1, y1, z1): #calulates the ElbowRoll value for the Left elbow by using geometry

        a1=(x3-x2)**2+(y3-y2)**2 + (z3-z2)**2
        lineA= a1 ** 0.5                        # calculates length of line between 2 3D coordinates
        b1=(x2-x1)**2+(y2-y1)**2 + (z2-z1)**2
        lineB= b1 ** 0.5                        # calculates length of line between 2 3D coordinates
        c1=(x1-x3)**2+(y1-y3)**2 + (z1-z3)**2
        lineC= c1 ** 0.5                        # calculates length of line between 2 3D coordinates

        cosB = (pow(lineA, 2) + pow(lineB,2) - pow(lineC,2))/(2*lineA*lineB)
        acosB = math.acos(cosB)
        angle = math.degrees(acosB)
        angle = -180+ angle
        return angle

    def nao_move(self, angle):
        # self.motion.setAngles(["HeadYaw", "HeadPitch"], [0.0, angle["HeadPitch"]], 0.3)
        self.motion.setAngles(["RShoulderPitch", "RShoulderRoll"], [angle["RShoulderPitch"],angle["RShoulderRoll"]], 0.3)
        self.motion.setAngles(["LShoulderPitch", "LShoulderRoll"], [angle["LShoulderPitch"],angle["LShoulderRoll"]], 0.3)
        self.motion.setAngles(["RElbowYaw", "RElbowRoll"], [angle["RElbowYaw"],angle["RElbowRoll"]], 0.3)
        self.motion.setAngles(["LElbowYaw", "LElbowRoll"], [angle["LElbowYaw"],angle["LElbowRoll"]], 0.3)

    def mirroring(self):
        start = time.time()
        while not self.stop_event.is_set():
            try:
                angle_rotation = {}
                joint_data = self.read_file()
                HeadPitch = self.angleHeadPitch(joint_data[2][0], joint_data[2][1],\
                joint_data[2][2], joint_data[3][0], joint_data[3][1], joint_data[3][2])
                # HeadRoll = angleHeadYaw(joint_data[2][0], joint_data[2][1],\
                # joint_data[2][2], joint_data[3][0], joint_data[3][1], joint_data[3][2])

                # shoulder pitch, rollともにshoulder, elbowの座標を入れる
                # この時、左右反転させる
                LShoulderPitch = self.angleLShoulderPitch(joint_data[8][0], joint_data[8][1],\
                joint_data[8][2], joint_data[9][0], joint_data[9][1], joint_data[9][2])
                LShoulderRoll = self.angleLShoulderRoll(joint_data[8][0], joint_data[8][1], \
                joint_data[8][2], joint_data[9][0], joint_data[9][1], joint_data[9][2])
                RShoulderPitch = self.angleRShoulderPitch(joint_data[4][0], joint_data[4][1],\
                joint_data[4][2], joint_data[5][0], joint_data[5][1], joint_data[5][2])
                RShoulderRoll = self.angleRShoulderRoll(joint_data[4][0], joint_data[4][1], \
                joint_data[4][2], joint_data[5][0], joint_data[5][1], joint_data[5][2])

                # ElbowYaw -> elbow, wristの座標を入れる
                LElbowYaw = self.angleLElbowYaw(joint_data[9][0], joint_data[9][1],\
                joint_data[9][2], joint_data[10][0], joint_data[10][1], joint_data[10][2],RShoulderPitch)
                # ElbowRoll -> shoulder, elbow, wristの座標を入れる
                LElbowRoll = self.angleLElbowRoll(joint_data[8][0], joint_data[8][1], joint_data[8][2], joint_data[9][0],\
                joint_data[9][1], joint_data[9][2], joint_data[10][0], joint_data[10][1], joint_data[10][2])
                RElbowYaw = self.angleRElbowYaw(joint_data[5][0], joint_data[5][1],\
                joint_data[5][2], joint_data[6][0], joint_data[6][1], joint_data[6][2],LShoulderPitch)
                RElbowRoll = self.angleRElbowRoll(joint_data[4][0], joint_data[4][1], joint_data[4][2], joint_data[5][0],\
                joint_data[5][1], joint_data[5][2], joint_data[6][0], joint_data[6][1], joint_data[6][2])

                # angle_rotation["HeadPitch"] = math.radians(HeadPitch)
                # angle_rotation["HeadYaw"] = math.radians(HeadYaw)
                # angle_rotation["RShoulderPitch"] = math.radians(RShoulderPitch)
                # angle_rotation["RShoulderRoll"] = math.radians(RShoulderRoll)
                # angle_rotation["LShoulderPitch"] = math.radians(LShoulderPitch)
                # angle_rotation["LShoulderRoll"] = math.radians(LShoulderRoll)
                # angle_rotation["RElbowYaw"] = math.radians(RElbowYaw)
                # angle_rotation["RElbowRoll"] = math.radians(RElbowRoll)
                # angle_rotation["LElbowYaw"] = math.radians(LElbowYaw)
                # angle_rotation["LElbowRoll"] = math.radians(LElbowRoll)

                # 動作量半分にしたいとき
                angle_rotation["RShoulderPitch"] = math.radians(RShoulderPitch/2)
                angle_rotation["RShoulderRoll"] = math.radians(RShoulderRoll/2)
                angle_rotation["LShoulderPitch"] = math.radians(LShoulderPitch/2)
                angle_rotation["LShoulderRoll"] = math.radians(LShoulderRoll/2)
                angle_rotation["RElbowYaw"] = math.radians(RElbowYaw/2)
                angle_rotation["RElbowRoll"] = math.radians(RElbowRoll/2)
                angle_rotation["LElbowYaw"] = math.radians(LElbowYaw/2)
                angle_rotation["LElbowRoll"] = math.radians(LElbowRoll/2)

                # print(angle_rotation)
                # naoをX秒毎に動かす
                self.nao_move(angle_rotation)
                elapsed_time = time.time() - start
                print("elapsed_time : {0}".format(elapsed_time) + "[sec]\n")
                # kinectのデータ取得間隔(0.045sec)に合わせる
                # programの処理自体が0.025secかかってしまうのでsleep(0.03)
                time.sleep(0.07)
            except Exception as e:
                print(e)
                print(">>> Bye")
                self.motion.rest()
                sys.exit(0)

    def speaking(self):
        speak = texttospeech.naoToSay()
        speak.main()
        time.sleep(3)
        print(">>> Scenario finished !")
        self.stop()
        self.motion.rest()


if __name__ == "__main__":
    mirror = naoMirroring()
