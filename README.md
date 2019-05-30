# 人脸识别考勤系统

## 演示
[演示视频](https://pan.baidu.com/s/19RRy_hT_Xyv9EZ-_BYDTEA "演示视频")

## 使用
```
python3 face.py
```

## 目录介绍
```
Project
|
+——— avatar -- 头像下载存储
|
+——— audio -- 音频文件下载
|
+——— back -- 打卡成功捕获的画面
|
|——— api -- 本地保留的接口文件
|
|——— config -- 软件接口配置：包含了1.本地更新打卡数据池的时间间隔（refreshconfigtime）；2.签到接口（addsign）；3.读取人脸识别配置接口（faceconfig）；4.打卡用户数据池（userlist）
|
|——— face.py -- 入口文件
```