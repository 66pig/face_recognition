# 人脸识别考勤系统

## 说明
软件的话从去年到现在，一直完美支持100人以上考勤，如果在编译过程中遇到了任何报错，可以给我留言，如果看到的话，我会免费提供解答。
当然啦，也可以给我发邮件：jiarui.xing@foxmail.com。备注：人脸识别考勤。

## 软件打包
软件打包可参考：[Python软件打包教程](https://segmentfault.com/a/1190000009827526 "Python软件打包教程")

## 效果
![软件运行截图](./screenshot.jpg "运行截图")

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
|
|——— video.mp4 -- 演示视频
```
