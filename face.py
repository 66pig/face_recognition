# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""
from Ui_test_01 import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import QSplashScreen, QPixmap, Qt
from PIL import Image, ImageDraw, ImageFont
import time
import face_recognition
import cv2
import json
import numpy
import urllib.request
import pygame
import os
import requests


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Class documentation goes here.
    """
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        
        ## 初始化人员数据api文件
        # 接口地址JSON
        self.config = {}
        ## 语音识别token
        self.tok= '24.7c1517e22e211c10e802917cea5a3933.2592000.1537013512.282335-11506871'
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("溜溜猪人脸识别系统") 
        window_pale = QtGui.QPalette() 
        # 这是软件背景图
        window_pale.setBrush(self.backgroundRole(),   QtGui.QBrush(QtGui.QPixmap("./static/llz_background.png"))) 
        self.setAutoFillBackground(True)
        self.setPalette(window_pale)
        # 存储网格布局对象，方便后期移动
        self.gridLayout_userlist_0 = self.gridLayoutWidget
        self.gridLayout_userlist_1 = self.gridLayoutWidget_2
        self.gridLayout_userlist_2 = self.gridLayoutWidget_3
        self.gridLayout_userlist_3 = self.gridLayoutWidget_4
        self.gridLayout_userlist_4 = self.gridLayoutWidget_5
        self.gridLayout_userlist_5 = self.gridLayoutWidget_6
        self.gridLayout_userlist_6 = self.gridLayoutWidget_8
        # 初始化面板资源
        self.init_resource()
        # cv2调用开启摄像头方法
        self.video_capture = cv2.VideoCapture(0)
        self.no_video = False
        # 下面是是人脸识别参数
        self.labels = []
        self.person = []
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True
        # 渲染摄像头进行对比相似度时，开的时间如果过快，而调用的对比函数还未执行完毕时，
        # 为了防止增加负荷，可以设置一个onoff_face开关
        # 当开始执行时，将值调整为False，进入方法（关门），执行结束后再打开开关允许下次执行（开门）
        self.onoff_face = True
        
        # 初始化可变变量
        self.names = locals()
        # 初始化时获取用户的数据
        # self.init_api()
        self.get_userinfo_fromapifile()
       
        # 设置两次签到的间隔时间，单位：秒
        self.sign_between = 16
        
        # 设置连续识别成功多少次方可进行签到数据写入（成功签到）
        self.rectimes = 1
        # 精确度调整，默认为0.39
        self.tolerance = 0.39
        # 签到成功后头像与信息从主界面消失的时间间隔
        self.avatar_between = 3
        
        # 捕捉到的图像参数，系数，以及放大倍数
        # 缩小系数与放大倍数的乘机必须为 1
        self.facefx = self.facefy = 0.5
        self.facescale = 2
        
        
        # 初始化时显示头像的布局隐藏
        self.verticalLayoutWidget_2.hide()
        self.label_userinfo_all_bg.hide()
        # 初始化考勤系统唤醒时tips隐藏
        self.label_shadow_tips.hide()
        # 初始化签到成功时的时间点
        self.avatar_time = int(time.time())
    
        
        # 签到列表组件对象
        self.sign_obj_list = {}
        # 签到列表组件对象位置
        self.sign_list = {}
        # 已签到用户列表
        self.sign_user_list = []
        # 初始化签到数据
        for i in range(7):
            self.sign_user_list.append({"avatar":"", "name":"", "userinfo":"", "signed":"", "time": "", "date":""})
        self.avatar_list_func()
        self.save_sign_pos_info()
        ######## 计时器 ########
        # 线程的信号连接一个函数槽
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.face_start) 
        # 连接头像计时器槽函数
        self.avatar_timer_sign = QtCore.QTimer()
        self.avatar_timer_sign.timeout.connect(self.avatar_timer_func)
        # 签到列表计时器槽函数
        self.pos_start_m = 0
        self.avatar_timer_sign_list = QtCore.QTimer()
        self.avatar_timer_sign_list.timeout.connect(self.sign_list_mover_func)
    
        # 更新配置文件槽函数
        self.refresh_faceconfig_timer = QtCore.QTimer()
        self.refresh_faceconfig_timer.timeout.connect(self.refresh_resource)
        # self.refresh_faceconfig_timer.start(self.config['refreshconfigtime'])
        # 开始启动摄像头图像渲染函数，start中为渲染时间间隔
        # 人眼能识别的帧数是30fps/s
        # 1000ms/30fps 约等于33ms
        # 所以这里将频率设置为30ms～34ms比较合适
        # 为了达到最佳，这里设置为了30
        self.timer.start(20)
        # 设置签到成功头像通过此计时器刷新来使用头像框（头像与信息）隐藏的函数
        self.avatar_timer_sign.start(2000)
        # 初始化签到列表
        self.init_sign_list()
        # 签到人数
        # self.sign_num = 0
        # 存用户签到成功时的数据
        self.this_avatar = ""
        self.this_name = ""
        self.this_rank = ""
        self.this_time = ""
        self.this_date = ""
        # 签到状态图片
        self.sign_status_pic = "./static/sign_status.png"
        ###################软件在使用过程中需要注意到的重点问题：资源占用！！！！#########################
        # 在一直频繁地调用摄像头，那么必然会造成资源的持续占用，在持续占用的过程中，如果都保持着较高地CPU使用率，
        # 将会导致系统运行缓慢，严重时还会发生系统崩溃等情况
        # 但，考勤签到的使用高峰期仅仅那么1～2小时，而且是断断续续地，为此而使得每天24小时都保持满负载CPU使用
        # 是极大资源浪费。
        # 对于这个问题，我的解决方案是：
        # 在无人使用的期间降低程序的运行速度，尽可能地减少CPU的使用，在使用时再激活其状态
        # 经过在MAC系统的测试（其它系统大体上相差不大，但是本次测试数据仅供参考）：
        # 速度为2s时，CPU使用率在6%～15%之间，平均峰值使用率为11%，无人使用时保持在10%
        # 速度为1s时，CPU使用率在11%～22%之间，平均峰值使用率为12%，
        # 速度为0.5s时，CPU使用在20%～33%之间，平均峰值使用率为17%
        # 方案：在15s内无人使用，程序自动降低运行速度（用专业点的文字来形容：软件休眠，但并不是真正地休眠，只是运行速度降低）
        # 这里，假设休眠时的速度为2s，那么如果在2s内识别到了人像，会自动（立即）激活其高频（正常）状态
        # ########################## 开始设置变量 #################################################
        # 时间点的判断需要用到两个变量：my_sleep_front、my_sleep_end
        # 如果2s内都未识别到人像，将进行自动休眠；
        self.my_sleep_front = int(time.time())
        # self.my_sleep_end = int(time.time()) 最新时间似乎用不上，其实可以直接取当前时间，这样可以减少变量
        # 但是休眠期间期间不需要进行时间判断，只有在激活状态才需要判断是否应该休眠，
        # 因此这里需要用到一个开关，my_sleep_onoff
        self.my_sleep_onoff = True
        # 设置变量，在my_sleep_time,多少秒内无响应，开始休眠,单位秒
        self.my_sleep_time = 6000000
        #########################################################################################
        # 初始化签到成功音频
        #         for user in self.user_info['result']:
        #             pygame.mixer.init(frequency=15500,size=-16,channels=4)       
        #             track = pygame.mixer.music.load("./audio/"+this_uid+".mp3")
        
       
        # self.refresh_resource()
        
        # 定义开关，如果是在更新资源，则不进行人脸识别函数的执行，直到数据更新结束再开始人脸识别
        self.refresh_facestart_onoff = True
        
    def get_userinfo_fromapifile(self):
        # 用utf8编码读取接口数据，并遍历到数组中
        f = open("./api",encoding='UTF-8')
        # 从接口文件读取用户数据
        self.user_info = json.loads(f.read())
        f.close()
        # 打印接口数据
        #print(self.user_info['result'])
        # 遍历用户数据到相应字典或其它变量中
        self.labels = [] # 每次使用前需要把存储的用户数据置空
        # 下面是是人脸识别参数
        self.labels = []
        self.person = []
        for user in self.user_info['result']:
            self.labels.append(user['name'])
            ## 下载照片
            if os.path.exists('./avatar/'+user['avatar_name']):
                pass
            # else:
                # self.download_avatar(user['avatar'], './avatar/'+user['avatar_name'])
            ################################################
            ## 设置用户头像位置
            user['avatar'] = './avatar/'+user['avatar_name']    
            ################################################
            ## 下载音频文件 #################################
            if os.path.exists('./audio/'+user['uid']+'.mp3'):
                pass
            else:
                self.init_audio(user['name'], './audio/'+user['uid']+'.mp3')
            ###############################################
            self.person.append(
                face_recognition.face_encodings(
                    face_recognition.load_image_file(user["avatar"]))[0])
        
        # 打印用户姓名数据
        # print(self.labels)
        # 存储签到者签到间隔的初始化时间
        for i in range(len(self.labels)):
            #is_signto是计算识别的次数，如果3帧内为同一人，则签到成功
            # 连续累计识别成功一定次数大于某个值才给予成功签到，此处的self.names['is_signto%s'%i]为累加变量
            self.names['is_signto%s'%i] = 0
            self.names['time_first%s'%i] = 0
            self.names['time_last%s'%i] = int(time.time())
        
    def refresh_resource(self):
        self.refresh_facestart_onoff = False
        url = self.config['faceconfig']
        headers = {'Accept': '*/*',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
               'X-Requested-With': 'XMLHttpRequest'}
        r = requests.post(url, data='', headers=headers)
        data = json.loads(r.text)
         # 设置签名
        self.label_notice.setText('通知：'+data['result']['notice']['notice'])
        initdata = data['result']['softconfig']
        # 设置两次签到的间隔时间，单位：秒
        self.sign_between = initdata['sign_between_t']
        # 设置连续识别成功多少次方可进行签到数据写入（成功签到）
        self.rectimes = initdata['rectimes']
        # 精确度调整，默认为0.39
        self.tolerance = initdata['tolerance']
        # 签到成功后头像与信息从主界面消失的时间间隔
        self.avatar_between = initdata['avatar_hide_t']
        # 捕捉到的图像参数，系数，以及放大倍数
        # 缩小系数与放大倍数的乘机必须为 1
        self.facefx = initdata['face_fx']
        self.facefy = initdata['face_fy']
        self.facescale = initdata['face_scale']
        # 设置变量，在my_sleep_time,多少秒内无响应，开始休眠,单位秒
        self.my_sleep_time = initdata['face_sleep']
        self.init_api()
        self.get_userinfo_fromapifile()
        self.refresh_facestart_onoff = True
    def init_resource(self):
        self.label_video_rect_bg.setStyleSheet("background-image:url(./static/llz_video_rect.png)")
        self.label_userinfo_all_bg.setStyleSheet("background-image:url(./static/llz_userinfo_all.png)")
        # 右侧签到列表框
        self.user_list_right_wraper.setStyleSheet("background-image:url(./static/llz_user_list_right_wraper.png)")
        self.user_list_right_wraper.setScaledContents(True)
        #.setPixmap(QtGui.QPixmap.fromImage(
        
        self.label_video_rect_bg.setScaledContents(True)
        self.label_userinfo_all_bg.setScaledContents(True)
        # 签到列表0
        self.label_list_bg_0.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_0.setScaledContents(True)
        # 签到列表1
        self.label_list_bg_1.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_1.setScaledContents(True)
        # 签到列表2
        self.label_list_bg_2.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_2.setScaledContents(True)
        # 签到列表3
        self.label_list_bg_3.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_3.setScaledContents(True)
         # 签到列表4
        self.label_list_bg_4.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_4.setScaledContents(True)
        # 签到列表5
        self.label_list_bg_5.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_5.setScaledContents(True)
        # 签到列表6
        self.label_list_bg_6.setStyleSheet("background-image:url(./static/llz_user_list_bg.png)")
        self.label_list_bg_6.setScaledContents(True)
        # 签到列表头像框0
        self.label_user_list_head_rect_0.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_0.setScaledContents(True)
        # 签到列表头像框1
        self.label_user_list_head_rect_1.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_1.setScaledContents(True)
        # 签到列表头像框2
        self.label_user_list_head_rect_2.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_2.setScaledContents(True)
        # 签到列表头像框3
        self.label_user_list_head_rect_3.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_3.setScaledContents(True)
        # 签到列表头像框4
        self.label_user_list_head_rect_4.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_4.setScaledContents(True)
        # 签到列表头像框5
        self.label_user_list_head_rect_5.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_5.setScaledContents(True)
        # 签到列表头像框6
        self.label_user_list_head_rect_6.setStyleSheet("background-image:url(./static/llz_user_list_head_rect.png)")
        self.label_user_list_head_rect_6.setScaledContents(True)
    ## 存储用户签到信息
    def save_sign_info(self,data):
        url = 'http://172.30.9.206/face/public/index.php/facerec/api/addsign'
        headers = {'Accept': '*/*',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
               'X-Requested-With': 'XMLHttpRequest'}
        r = requests.post(url, data=data, headers=headers)
        # print(r.text)
    ## 下载照片（头像）
    def download_avatar(self, url, filename):
        # print(url)
        response = urllib.request.urlopen(url)
        html = response.read()
        
        f = open(filename, 'wb')
        f.write(html)
        f.close()
    ## 获取接口信息
    def init_api(self):
        # 用utf8编码读取接口地址
        fa = open("./config",encoding='UTF-8')
        # 从接口文件读取用户数据
        self.config = json.loads(fa.read())
        url = self.config['userlist']
        fa.close()
        response = urllib.request.urlopen(url)
        html = response.read()
        f = open('./api', 'wb')
        f.write(html)
        f.close()
    ## 下载音频
    def init_audio(self, stra, filename):
        def url_open(url):
            # req = urllib.request.Request(url)
            # req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36')
            response = urllib.request.urlopen(url)
            html = response.read()
        
            return html
        strb = '欢迎'+stra+'光临中冶铜锣台'
        strb =  urllib.parse.quote(strb)
        curl = "http://tsn.baidu.com/text2audio?lan=zh&ctp=1&cuid=abcdxxx&tok=%s&tex=%s&vol=9&per=0&spd=6&pit=5"%(self.tok,strb)
        img = url_open(curl)
        f = open(filename, 'wb')
        f.write(img)
        f.close()
    def avatar_timer_func(self):
        # 最后一次签到成功的时间距离现在是否超过self.avatar_between秒
        # 如果超过，则执行下面的操作关闭verticalLayoutWidget（这里面是是wraper的签到这的图片与信息）
        if(int(time.time()) - self.avatar_time > self.avatar_between):
            self.verticalLayoutWidget_2.hide()
            self.label_userinfo_all_bg.hide()
    # 专门用于存放头像的函数方法
    def add_user_info_to_arr_func(self, this_avatar, this_name,  this_department, issigned, this_time, this_date):
        # 向数组中存放签到数据
        self.sign_user_list.append({"avatar":this_avatar, 
                                     "name":this_name, 
                                     "userinfo": this_department, 
                                     "signed":self.sign_status_pic, 
                                     "time": this_time, 
                                     "date":this_date})
    def init_sign_list(self):
        
        a = len(self.sign_user_list)
        b = 0
        while b < 7:
            a -= 1
            # 头像
            self.sign_obj_list['label_list_avatar'][b].setStyleSheet(
                "border-image: url("+self.sign_user_list[a]['avatar']+");")
            # 姓名
            self.sign_obj_list['label_user_list_name'][b].setText(
                self.sign_user_list[a]['name'])
            # 部门
            self.sign_obj_list['label_user_list_dept'][b].setText(
                self.sign_user_list[a]['userinfo'])
            # 签到状态
            # self.sign_obj_list['label_user_list_head_rect'][b].setStyleSheet(
            #     "border-image: url("+self.sign_user_list[a]['signed']+");")
            # 签到时间
            self.sign_obj_list['label_user_list_time'][b].setText(
                self.sign_user_list[a]['time'])
            #签到日期
            self.sign_obj_list['label_user_list_date'][b].setText(
                self.sign_user_list[a]['date'])
            b+=1
        #重置签到位置
        for i in range(7):
            # 背景位置
            self.sign_obj_list['label_list_bg'][i].move(
                int(self.sign_list['label_list_bg_x'][i]), 
                int(self.sign_list['label_list_bg_y'][i]))
            # 头像位置
            # self.sign_obj_list['label_list_avatar'][i].move(
                # int(self.sign_list['label_list_avatar_x'][i]), 
                # int(self.sign_list['label_list_avatar_y'][i]))
            # 姓名位置
            # self.sign_obj_list['label_user_list_name'][i].move(
                # int(self.sign_list['label_user_list_name_x'][i]), 
                # int(self.sign_list['label_user_list_name_y'][i]))
            # 用户信息位置
            self.sign_obj_list['gridLayout_userlist'][i].move(
                int(self.sign_list['gridLayout_userlist_x'][i]), 
                int(self.sign_list['gridLayout_userlist_y'][i]))
            # 用户头像框位置
            self.sign_obj_list['label_user_list_head_rect'][i].move(
                int(self.sign_list['label_user_list_head_rect_x'][i]), 
                int(self.sign_list['label_user_list_head_rect_y'][i]))
            # 签到时间
            # self.sign_obj_list['label_user_list_time'][i].move(
                # int(self.sign_list['label_user_list_time_x'][i]), 
                # int(self.sign_list['label_user_list_time_y'][i]))
            #签到日期
            # self.sign_obj_list['label_user_list_date'][i].move(
                # int(self.sign_list['label_user_list_date_x'][i]), 
                # int(self.sign_list['label_user_list_date_y'][i]))
        
        # 签到列表动效时间函数
    def sign_list_mover_func(self, pos=40):
#         print(self.pos_start_m)
        # 签到列表移动动效的移动步幅
        self.pos_start_m += 10
        if self.pos_start_m > pos:
            self.pos_start_m = 0
            self.avatar_timer_sign_list.stop()
            self.init_sign_list()
            return
        for i in range(7):
                # 如果仅仅做垂直方向上的动效，为了节省资源，可以不存储水平位置，因为水平位置不会变动
                # 背景位置
                self.sign_obj_list['label_list_bg'][i].move(
                    int(self.sign_list['label_list_bg_x'][i]), 
                    int(self.sign_list['label_list_bg_y'][i])+self.pos_start_m)
                # 头像位置
                # self.sign_obj_list['label_list_avatar'][i].move(
                    # int(self.sign_list['label_list_avatar_x'][i]), 
                    # int(self.sign_list['label_list_avatar_y'][i])+self.pos_start_m)
                # 姓名位置
                # self.sign_obj_list['label_user_list_name'][i].move(
                    # int(self.sign_list['label_user_list_name_x'][i]), 
                    # int(self.sign_list['label_user_list_name_y'][i])+self.pos_start_m)
                # 用户信息位置
                self.sign_obj_list['gridLayout_userlist'][i].move(
                    int(self.sign_list['gridLayout_userlist_x'][i]), 
                    int(self.sign_list['gridLayout_userlist_y'][i])+self.pos_start_m)
                # 签到状态位置
                self.sign_obj_list['label_user_list_head_rect'][i].move(
                    int(self.sign_list['label_user_list_head_rect_x'][i]), 
                    int(self.sign_list['label_user_list_head_rect_y'][i])+self.pos_start_m)
                # 签到时间
                # self.sign_obj_list['label_user_list_time'][i].move(
                    # int(self.sign_list['label_user_list_time_x'][i]), 
                    # int(self.sign_list['label_user_list_time_y'][i])+self.pos_start_m)
                # 签到日期
                # self.sign_obj_list['label_user_list_date'][i].move(
                    # int(self.sign_list['label_user_list_date_x'][i]), 
                    # int(self.sign_list['label_user_list_date_y'][i])+self.pos_start_m)

    # 签到列表的动效处理函数，参数pos为移动的位置，uid为用户id
    def move_sign_list_pos(self):
        # 存签到人数
        # self.sign_num += 1
        # self.label_54.setText(str(self.sign_num))
        self.init_sign_list()
        # 开始存最新数据
        self.add_user_info_to_arr_func(
            self.this_avatar, 
            self.this_name, 
            self.this_department, "", 
            self.this_time, 
            self.this_date)
        self.pos_start_m = 0
        self.avatar_timer_sign_list.stop()
        self.avatar_timer_sign_list.start(60)
        # 当移动动一定位置后，更新签到列表数据
        
    # 存储签到列表初始化位置信息
    def save_sign_pos_info(self):
        # 存储签到面板说有模块的对象，方便后期循环遍历使用
        # 背景对象
        self.sign_obj_list['label_list_bg'] = []
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_0)
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_1)
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_2)
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_3)
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_4)
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_5)
        self.sign_obj_list['label_list_bg'].append(self.label_list_bg_6)
        # 头像对象
        self.sign_obj_list['label_list_avatar'] = []
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_0)
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_1)
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_2)
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_3)
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_4)
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_5)
        self.sign_obj_list['label_list_avatar'].append(self.label_list_avatar_6)
        # 姓名对象
        self.sign_obj_list['label_user_list_name'] = []
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_0)
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_1)
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_2)
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_3)
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_4)
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_5)
        self.sign_obj_list['label_user_list_name'].append(self.label_user_list_name_6)
        # 用户部门对象
        self.sign_obj_list['label_user_list_dept'] = []
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_0)
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_1)
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_2)
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_3)
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_4)
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_5)
        self.sign_obj_list['label_user_list_dept'].append(self.label_user_list_dept_6)
        # 用户信息布局对象
        self.sign_obj_list['gridLayout_userlist'] = []
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_0)
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_1)
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_2)
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_3)
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_4)
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_5)
        self.sign_obj_list['gridLayout_userlist'].append(self.gridLayout_userlist_6)
        # 签到状态对象
        self.sign_obj_list['label_user_list_head_rect'] = []
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_0)
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_1)
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_2)
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_3)
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_4)
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_5)
        self.sign_obj_list['label_user_list_head_rect'].append(self.label_user_list_head_rect_6)
        
        # 签到时间对象
        self.sign_obj_list['label_user_list_time'] = []
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_0)
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_1)
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_2)
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_3)
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_4)
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_5)
        self.sign_obj_list['label_user_list_time'].append(self.label_user_list_time_6)
        #签到日期
        self.sign_obj_list['label_user_list_date'] = []
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_0)
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_1)
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_2)
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_3)
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_4)
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_5)
        self.sign_obj_list['label_user_list_date'].append(self.label_user_list_date_6)
        
        # 初始化存储位置信息的数组
        # 背景
        self.sign_list['label_list_bg_x'] = []
        self.sign_list['label_list_bg_y'] = []
        # 头像
        # self.sign_list['label_list_avatar_x'] = []
        # self.sign_list['label_list_avatar_y'] = []
        # 姓名
        # self.sign_list['label_user_list_name_x'] = []
        # self.sign_list['label_user_list_name_y'] = []
        # 用户信息
        self.sign_list['gridLayout_userlist_x'] = []
        self.sign_list['gridLayout_userlist_y'] = []
        # 签到状态
        self.sign_list['label_user_list_head_rect_x'] = []
        self.sign_list['label_user_list_head_rect_y'] = []
        # 签到时间
        # self.sign_list['label_user_list_time_x'] = []
        # self.sign_list['label_user_list_time_y'] = []
        #签到日期
        # self.sign_list['label_user_list_date_x'] = []
        # self.sign_list['label_user_list_date_y'] = []
        
        # 遍历存储签到列表所有模块位置信息
        for i in range(7):
            # 如果仅仅做垂直方向上的动效，为了节省资源，可以不存储水平位置，因为水平位置不会变动
            # 背景位置
            self.sign_list['label_list_bg_x'].append(self.sign_obj_list['label_list_bg'][i].x())
            self.sign_list['label_list_bg_y'].append(self.sign_obj_list['label_list_bg'][i].y())
            # 头像位置
            # self.sign_list['label_list_avatar_x'].append(self.sign_obj_list['label_list_avatar'][i].x())
            # self.sign_list['label_list_avatar_y'].append(self.sign_obj_list['label_list_avatar'][i].y())
            # 姓名位置
            # self.sign_list['label_user_list_name_x'].append(self.sign_obj_list['label_user_list_name'][i].x())
            # self.sign_list['label_user_list_name_y'].append(self.sign_obj_list['label_user_list_name'][i].y())
            # 用户信息位置
            self.sign_list['gridLayout_userlist_x'].append(self.sign_obj_list['gridLayout_userlist'][i].x())
            self.sign_list['gridLayout_userlist_y'].append(self.sign_obj_list['gridLayout_userlist'][i].y())
            # 签到状态位置
            self.sign_list['label_user_list_head_rect_x'].append(self.sign_obj_list['label_user_list_head_rect'][i].x())
            self.sign_list['label_user_list_head_rect_y'].append(self.sign_obj_list['label_user_list_head_rect'][i].y())
            # 签到时间
            # self.sign_list['label_user_list_time_x'].append(self.sign_obj_list['label_user_list_time'][i].x())
            # self.sign_list['label_user_list_time_y'].append(self.sign_obj_list['label_user_list_time'][i].y())
            #签到日期
            # self.sign_list['label_user_list_date_x'].append(self.sign_obj_list['label_user_list_date'][i].x())
            # self.sign_list['label_user_list_date_y'].append(self.sign_obj_list['label_user_list_date'][i].y())
        
        # print(self.sign_list)
    def avatar_list_func(self):
        pass
    # 渲染摄像头函数   
    def face_start(self):
        if self.refresh_facestart_onoff == False:
            return
        # 渲染右上角的时间与日期
        self.label_right_top_time.setText(time.strftime("%H:%M",time.localtime(time.time())))
        self.label_right_top_date.setText('['+time.strftime("%Y-%m-%d",time.localtime(time.time()))+']')
        
        #if(int(time.time()) - self.avatar_time > 3):
        #    self.verticalLayoutWidget.hide()
        if self.onoff_face:
            
            ############# 判断是否进行休眠 ##############
            if self.my_sleep_onoff:
                self.my_sleep_end = int(time.time())
                if (int(time.time()) - self.my_sleep_front) > self.my_sleep_time:
                    # 休眠状态时，提示唤醒tips
                    self.label_shadow_tips.show()
                    self.my_sleep_onoff = False
                    self.timer.stop()
                    self.timer.start(2000)
            
            self.onoff_face = False
            # 判断摄像头是否插入，如果未插入，需要重新检测，检测的同时关闭入口
            # 直到下次读取摄像画面失败再开启
            if self.no_video == True:
                self.no_video = False
                self.video_capture = cv2.VideoCapture(0)
            # 读取摄像头画面
            ret, frame = self.video_capture.read()
            if ret == False:
                self.no_video = True
                self.onoff_face = True
                return
            
            # 画面水平翻转
            frame = cv2.flip(frame, 1)
            # 改变摄像头图像的大小，图像小，所做的计算就少
#             small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            small_frame = cv2.resize(frame, (0, 0), fx=self.facefx, fy=self.facefy)
            #cv2.imwrite('./messigray.png',small_frame)
            # small_frame = frame
            # Only process every other frame of video to save time
            if self.process_this_frame:
                # 根据encoding来判断是不是同一个人，是就输出true，不是为flase
                # face_locations为摄像头中捕捉到的人像的坐标数组
                self.face_locations = face_recognition.face_locations(small_frame)
                # 通过坐标提取摄像头中的人像数据
                self.face_encodings = face_recognition.face_encodings(small_frame, self.face_locations)
                # 存储识别到的人像的姓名，或者其它数据，类型为数组
                self.face_names = []
                name = ""
                
                for face_encoding in self.face_encodings:
                    # 如果程序走到这一步，说明摄像头中出现了人像，此时需要更新休眠期间人像判断的时间值
                    if self.my_sleep_onoff == False:
                        self.my_sleep_onoff = True
                        self.timer.stop()
                        self.timer.start(30)
                        # 唤醒状态时，隐藏tips提示
                        self.label_shadow_tips.hide()
                    # compare_faces方法对比查找人像函数（找相似），
                    # 参数1表示要查找的（本地的）人像，
                    # 参数2表示从摄像头取出的带有人像（或者是没有都可以，如果没有，那么就自动会返回False）
                    # 参数3 tolerance表示识别人像的精度，数值越小，进度越高，参数越大精度越小，识别越模糊，最大为1，最小为0
                    match = face_recognition.compare_faces(self.person, face_encoding,tolerance=self.tolerance)
#                     print(match)
                   
                    self.my_sleep_front = int(time.time())  
                    for i in range(len(match)):

                        if match[i]:
                            self.names['is_signto%s'%i] += 1
                            # 获取当前时间
                            self.names['time_last%s'%i] = int(time.time())
                            # 存放一些局部临时变量，方便后面的多次使用
                            this_uid = self.user_info['result'][i]['uid']
                            this_name = self.user_info['result'][i]['name']
                            this_sex = self.user_info['result'][i]['sex']
                            this_age = str(self.user_info['result'][i]['age'])
                            this_avatar = self.user_info['result'][i]['avatar']
                            this_rank = self.user_info['result'][i]['rank']
                            this_department = self.user_info['result'][i]['department']
                            this_slogan = self.user_info['result'][i]['slogan']
                            # 处理一下name值，此时它不再是只包含姓名数据，它代表了将要实时显示的所有信息
                            name = this_name +\
                                "\n"+\
                                this_department
                            # 连续累计识别成功一定次数大于某个值才给予成功签到
                            if self.names['is_signto%s'%i] > self.rectimes:
                                # 第一次签到的时间和现在相差小于一定时间段内，无法再次签到
                                if (self.names['time_last%s'%i] - self.names['time_first%s'%i]) > self.sign_between:
                                    self.names['is_signto%s'%i] = 0
                                    # 签到成功，存数据，存一些全局变量，方便函数内多次调用（一下基本上都是存的签到页面需要用的的数据）
                                    self.this_name = this_name
                                    self.this_avatar = this_avatar
                                    self.this_rank = this_rank
                                    self.this_department = this_department
                                    
                                    self.this_time = time.strftime("%H:%M",time.localtime(self.names['time_last%s'%i]))
                                    self.this_date = time.strftime("%Y-%m-%d",time.localtime(self.names['time_last%s'%i]))
                                    
                                    # 读取签到成功的音频文件
                                    pygame.mixer.init(frequency=15500,size=-16,channels=4)       
                                    track = pygame.mixer.music.load("./audio/"+this_uid+".mp3")
                                    pygame.mixer.music.play()
                                    # 签到成功，调用签到列表的动效函数
                                    self.move_sign_list_pos()
                                    #self.textBrowser.append(this_rank+">"+this_name+":签到成功")
                                    self.label_2.setStyleSheet("border-image: url("+this_avatar+");")
                                    #self.label_4.setText(this_name)
                                    # 设置名字
                                    self.label_userinfo_all_name.setText('姓名：'+this_name)
                                    # 设置性别
                                    self.label_userinfo_all_sex.setText('性别：'+this_sex)
                                    # 设置年龄
                                    self.label_userinfo_all_age.setText('年龄：'+this_age)
                                    # 设置职位
                                    self.label_userinfo_all_rank.setText('职位：'+this_rank)
                                    # 设置部门
                                    self.label_userinfo_all_dept.setText('部门：'+this_department)
                                    # 设置签名
                                    self.label_userinfo_all_slogan.setText('签名：'+this_slogan)
                                    # 计时器
                                    self.avatar_time = int(time.time())
                                    # 显示头像框的布局
                                    self.verticalLayoutWidget_2.show()
                                    self.label_userinfo_all_bg.show()
                                    # 存储用户的签到数据
                                    # self.save_sign_info({'signout_t': self.names['time_last%s'%i], 'uid':this_uid})
                                    # 签到成功后将最新签到时间更新，方便下次对比
                                    self.names['time_first%s'%i] = self.names['time_last%s'%i]
                                else:
                                    pass
                            
                            # 只要识别到了就跳出循环，
                            # 未识别到就执行else语句，将相似度低的全部设为undefined
                            # 这样就会减少误识率
                            break
                        else:
                            # 如果某一次没识别上就重置变量，让一段时间累计叠加的识别成功次数归零（重置）
                            self.names['is_signto%s'%i] = 0
                            # 在一次循环的匹配中，如果一个人都没有匹配上，那么说明这个人未录入信息
                            # 此时需要给予这个人一个undefined信息，这里用了who->变量
                            name = ""
                        
                    # 保存当前识别的人脸的姓名或（以及）其它数据
                    self.face_names.append(name)
            self.process_this_frame = not self.process_this_frame
            
            # 将捕捉到的人脸显示出来
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                # 绘制出的人脸四个方角的坐标点
                top *= self.facescale
                right *= self.facescale
                bottom *= self.facescale
                left *= self.facescale
                
                top = int(top)
                right = int(right)
                bottom = int(bottom)
                left = int(left)
#                 cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 255),  3)
                # 通过四个坐标点计算出方框的1/3宽，以方便后面绘制框出人脸的线条
                right_left_between = int((right-left)/5)
                #### 绘制四根线条
                # 顶部线条
                cv2.line(frame,(left, top),(left+right_left_between, top), (255, 255, 255),  2)
                cv2.line(frame,(right, top),(right-right_left_between, top), (255, 255, 255),  2)
                # 底部线条
                cv2.line(frame,(left, bottom),(left+right_left_between, bottom), (255, 255, 255),  2)
                cv2.line(frame,(right, bottom),(right-right_left_between, bottom), (255, 255, 255),  2)
                # 左侧线条
                cv2.line(frame,(left, top),(left, top+right_left_between), (255, 255, 255),  2)
                cv2.line(frame,(left, bottom),(left,bottom-right_left_between), (255, 255, 255),  2)
                # 右侧线条
                cv2.line(frame,(right, top),(right, top+right_left_between), (255, 255, 255),  2)
                cv2.line(frame,(right, bottom),(right,bottom-right_left_between), (255, 255, 255),  2)
#                 cv2.rectangle(frame, (left, bottom - 65), (right, bottom), (255, 255, 255), 5)
#                 font = cv2.FONT_HERSHEY_DUPLEX
                # if frame != None:
                # frame = ft.draw_text(frame, (left+16, bottom-50), name, 34, (255, 255, 255))
                # 调用中文处理函数，默认字体大小为最后一个参数：22
                frame = self.cv2ImgAddText(frame, name, left+5, bottom-37, (255, 255, 255), 12)
            # cv2.imshow('Video', frame)
        
#                 cv2.putText(frame, name, (left+6, bottom-6), font, 1.0, (255, 255, 255), 1)
    #        下方是一种最笨的办法实时显示图片：写入到文件，展示文件
    #         cv2.imwrite('./messigray.png',frame)
    #         self.label.setStyleSheet("border-image: url(./messigray.png);")
            show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_3.setPixmap(QtGui.QPixmap.fromImage(showImage))
            #图像缩放：使用label的setScaledContents(True)方法，自适应label大小
            self.label_3.setScaledContents(True)
    #             cv2.imshow('Video', frame)
            self.onoff_face = True
        else:
            # print(self.onoff_face)
            pass
    
    # 中文处理函数
    def cv2ImgAddText(self, img, text, left, top, textColor=(0, 255, 0), textSize=20):
        if (isinstance(img, numpy.ndarray)):  #判断是否OpenCV图片类型
            img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        fontText = ImageFont.truetype(
            # 参数1:字体文件路径，默认设定好，避免后期增加传参复杂度
            "msyh.ttf", textSize, encoding="utf-8")
        draw.text((left, top), text, textColor, font=fontText)
        return cv2.cvtColor(numpy.asarray(img), cv2.COLOR_RGB2BGR)
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # 启动界面
    splash=QSplashScreen(QPixmap("./static/liuliuzhulogo.png"))
    splash.show()
    splash.showMessage(u'正在加载资源……\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t\n\t', Qt.AlignCenter, Qt.white)
    app.processEvents()
    ui = MainWindow()
    ui.show()
    splash.finish(ui)
    sys.exit(app.exec_())
