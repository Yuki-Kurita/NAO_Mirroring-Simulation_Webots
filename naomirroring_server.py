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
import socket

class naoMirroring():
    def __init__(self):
        # -- nao setup --#
        IP = "163.221.124.196"
        user_name = 'nao'
        self.motion = ALProxy("ALMotion", IP, 9559)
        self.tracker = ALProxy("ALTracker", IP, 9559)
        self.motion.wakeUp()
        self.motion.setStiffnesses("Head", 1.0)
        self.motion.setStiffnesses("Body", 1.0)
        # -- 顔の自動検出をなくしたい --
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

    def read_file(self):
        k_dic = {}
        file_loop = 0
        # 同じ階層のファイルで一番新しいファイルを読み込む
        files = os.listdir('C:\Users\P4\workspace\mirroring\data')
        latest_no = max([int(i.split(".")[0]) for i in files])
        latest_file = 'data/' + str(latest_no) + '.txt'
        # 動きを滑らかにするために、前2つのファイルを読み込む
        one_before_file = 'data/' + str(latest_no - 30) + '.txt'
        two_before_file = 'data/' + str(latest_no - 60) + '.txt'

        for file in [latest_file, one_before_file, two_before_file]:
            file_loop += 1
            with open(file, 'r') as f:
                for line in f:
                    k_items = line.split(",")
                    if file_loop == 1:
                        k_dic[int(k_items[0])] = [float(k_items[1]), float(k_items[2]), float(k_items[3])]
                    else:
                        k_dic[int(k_items[0])] = [k_dic[int(k_items[0])][0] + float(k_items[1]),\
                        k_dic[int(k_items[0])][1] + float(k_items[2]), k_dic[int(k_items[0])][2] + float(k_items[3])]
        for k, v in k_dic.items():
            k_dic[k] = [i/3 for i in v]
        return k_dic

    def tcpip_config(self):
        k_dic = {}
        host = "163.221.38.217" #お使いのサーバーのホスト名を入れます
        port = 9876 #クライアントで設定したPORTと同じもの指定してあげます
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversock.bind((host,port)) #IPとPORTを指定してバインドします
        serversock.listen(10) #接続の待ち受けをします（キューの最大数を指定）

        print ('Waiting for connections...')
        clientsock, client_address = serversock.accept() #接続されればデータを格納

        return clientsock

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
        i = 0
        clientsock = self.tcpip_config() # tcpip通信の設定
        # joint_data = self.read_file() # fileから読み込みする場合
        # server側で、データを受け取る

        while True:
            try:
                joint_data = {}
                angle_rotation = {}
                rcvmsg = clientsock.recv(1024)
                if rcvmsg == '':
                    break
                kinect_raw_list = rcvmsg.split('e')[0].splitlines()

                if len(kinect_raw_list) == 16:
                    # dictionaryの型に変換する
                    for raw_data_set in kinect_raw_list:
                        i += 1
                        raw_data = raw_data_set.split(",")
                        if(i == 1):
                            joint_data[1] = [float(raw_data[1]), float(raw_data[2]), float(raw_data[3])]
                        else:
                            joint_data[int(raw_data[0])] = [float(raw_data[1]), float(raw_data[2]), float(raw_data[3])]

                    # ----- nao の関節角を求める ----- #
                    # HeadPitch = self.angleHeadPitch(joint_data[2][0], joint_data[2][1],\
                    # joint_data[2][2], joint_data[3][0], joint_data[3][1], joint_data[3][2])
                    # HeadYaw = self.angleHeadYaw(joint_data[2][0], joint_data[2][1],\
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
                    angle_rotation["RShoulderPitch"] = math.radians(RShoulderPitch)
                    angle_rotation["RShoulderRoll"] = math.radians(RShoulderRoll)
                    angle_rotation["LShoulderPitch"] = math.radians(LShoulderPitch)
                    angle_rotation["LShoulderRoll"] = math.radians(LShoulderRoll)
                    angle_rotation["RElbowYaw"] = math.radians(RElbowYaw)
                    angle_rotation["RElbowRoll"] = math.radians(RElbowRoll)
                    angle_rotation["LElbowYaw"] = math.radians(LElbowYaw)
                    angle_rotation["LElbowRoll"] = math.radians(LElbowRoll)

                    #naoをX秒毎に動かす
                    self.nao_move(angle_rotation)
                    #time.sleep(0.4)
                    i = 0
                # 送信するmessage
                s_msg = "ok"
                clientsock.sendall(s_msg) #メッセージを返します

            except Exception as e:
                print(e)
                print(">>> Bye")
                self.motion.rest()
                clientsock.close()
                sys.exit(0)

        clientsock.close()

    def speaking(self):
        speak = texttospeech.naoToSay()
        speak.main()
        time.sleep(3)
        print(">>> Scenario finished !")
        self.stop()
        self.motion.rest()


if __name__ == "__main__":
    mirror = naoMirroring()

# host = "163.221.38.217" #お使いのサーバーのホスト名を入れます
# port = 9876 #クライアントで設定したPORTと同じもの指定してあげます
#
# serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# serversock.bind((host,port)) #IPとPORTを指定してバインドします
# serversock.listen(10) #接続の待ち受けをします（キューの最大数を指定）
#
# print 'Waiting for connections...'
# clientsock, client_address = serversock.accept() #接続されればデータを格納
#
# while True:
#     # 受け取ったmessage
#     rcvmsg = clientsock.recv(1024)
#     print('---------')
#     print(rcvmsg.split('e')[0])
#     print('---------')
#     if rcvmsg == '':
#       break
#     # 送信するmessage
#     s_msg = "ok"
#
#     clientsock.sendall(s_msg) #メッセージを返します
# clientsock.close()
