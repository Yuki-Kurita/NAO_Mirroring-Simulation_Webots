# coding:utf-8
import sys
import os
import time
import math
import datetime

class convertMotionFile():
    def __init__(self):
        # input file
        self.directory = "./video_experiment/taiwasha2/"
        # output file
        self.motion_file_name = "./motions/sample.motion"
        self.file_no = 60
        self.HeadPitch = 0
        self.motion_counter = 0

    def read_file(self):
        k_dic = {}
        file_loop = 0
        line_count = 0
        file_name = self.directory + str(self.file_no) + '.txt'
        # 動きを滑らかにするために、前2つのファイルを読み込む
        one_before_file = self.directory + str(self.file_no - 20) + '.txt'
        two_before_file = self.directory + str(self.file_no - 40) + '.txt'

        for file in [file_name, one_before_file, two_before_file]:
            file_loop += 1
            with open(file, 'r') as f:
                for line in f:
                    # time抽出
                    if line_count == 16 and file_loop == 1:
                        timestamp = int(line)
                        break
                    elif line_count == 16:
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
        return k_dic, timestamp

    def writeMotionFile(self, angle_rotation, timestamp):
        with open(self.motion_file_name, 'a', newline="\n") as f:
            if self.motion_counter == 0:
                f.write("#WEBOTS_MOTION,V1.0,RShoulderPitch,RShoulderRoll,LShoulderPitch,LShoulderRoll,RElbowYaw,RElbowRoll,LElbowYaw,LElbowRoll\n")
                self.timestamp = timestamp
            else:
                # poseの間の時間を導出
                div_time = (timestamp - self.timestamp)/10
                td = "0" + str(datetime.timedelta(seconds = div_time)).replace(".", "")[:8]
                if len(td) == 8:
                    td += "0"
                pose = "Pose" + str(self.motion_counter)
                # 時刻, poseの順など並べてファイルに書き足す
                f.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\n".format(td, pose, angle_rotation["RShoulderPitch"], angle_rotation["RShoulderRoll"], angle_rotation["LShoulderPitch"],
                angle_rotation["LShoulderRoll"], angle_rotation["RElbowYaw"], angle_rotation["RElbowRoll"], angle_rotation["LElbowYaw"], angle_rotation["LElbowRoll"]))
            self.motion_counter += 1

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

    def run(self):
        num_of_files = len([name for name in os.listdir(self.directory)]) - 2
        for i in range(num_of_files):
            try:
                angle_rotation = {}
                joint_data, timestamp = self.read_file()
                self.LShoulderPitch = self.angleLShoulderPitch(joint_data[8][0], joint_data[8][1],\
                joint_data[8][2], joint_data[9][0], joint_data[9][1], joint_data[9][2])
                self.LShoulderRoll = self.angleLShoulderRoll(joint_data[8][0], joint_data[8][1], \
                joint_data[8][2], joint_data[9][0], joint_data[9][1], joint_data[9][2])
                self.RShoulderPitch = self.angleRShoulderPitch(joint_data[4][0], joint_data[4][1],\
                joint_data[4][2], joint_data[5][0], joint_data[5][1], joint_data[5][2])
                self.RShoulderRoll = self.angleRShoulderRoll(joint_data[4][0], joint_data[4][1], \
                joint_data[4][2], joint_data[5][0], joint_data[5][1], joint_data[5][2])

                # ElbowYaw -> elbow, wristの座標を入れる
                self.LElbowYaw = self.angleLElbowYaw(joint_data[9][0], joint_data[9][1],\
                joint_data[9][2], joint_data[10][0], joint_data[10][1], joint_data[10][2],self.RShoulderPitch)
                # ElbowRoll -> shoulder, elbow, wristの座標を入れる
                self.LElbowRoll = self.angleLElbowRoll(joint_data[8][0], joint_data[8][1], joint_data[8][2], joint_data[9][0],\
                joint_data[9][1], joint_data[9][2], joint_data[10][0], joint_data[10][1], joint_data[10][2])
                self.RElbowYaw = self.angleRElbowYaw(joint_data[5][0], joint_data[5][1],\
                joint_data[5][2], joint_data[6][0], joint_data[6][1], joint_data[6][2],self.LShoulderPitch)
                self.RElbowRoll = self.angleRElbowRoll(joint_data[4][0], joint_data[4][1], joint_data[4][2], joint_data[5][0],\
                joint_data[5][1], joint_data[5][2], joint_data[6][0], joint_data[6][1], joint_data[6][2])

                angle_rotation["RShoulderPitch"] = round(math.radians(self.RShoulderPitch), 5)
                angle_rotation["RShoulderRoll"] = round(math.radians(self.RShoulderRoll), 5)
                angle_rotation["LShoulderPitch"] = round(math.radians(self.LShoulderPitch), 5)
                angle_rotation["LShoulderRoll"] = round(math.radians(self.LShoulderRoll), 5)
                angle_rotation["RElbowYaw"] = round(math.radians(self.RElbowYaw), 5)
                angle_rotation["RElbowRoll"] = round(math.radians(self.RElbowRoll), 5)
                angle_rotation["LElbowYaw"] = round(math.radians(self.LElbowYaw), 5)
                angle_rotation["LElbowRoll"] = round(math.radians(self.LElbowRoll), 5)
                # motionファイルに書き出し
                self.writeMotionFile(angle_rotation, timestamp)

            except Exception as e:
                print(e)
                print(">>> Bye")
                sys.exit(0)


convert = convertMotionFile()
convert.run()
