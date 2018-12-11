from pserver import random_string  # 导入获取随机密钥的方法
from pserver import Node, UNHANDLED  # 导入节点类和请求状态变量
from xmlrpc.client import ServerProxy, Fault
from threading import Thread
from time import sleep
import wx  # 导入wxPython模块
import sys
import os
import subprocess

HEAD_START = 0.1
SECRET_LENGTH = 10

class ListableNode(Node):  # 定义Node子类
    def file_list(self):  # 定义获取文件列表的方法
        return os.listdir(self.dirname)  # 返回文件列表

class Client(wx.App):  # 定义客户端类
    def __init__(self, url_file, dir_name, url):  # 定义构造方法
        self.dir_name = dir_name
        self.secret = random_string(SECRET_LENGTH)
        node = ListableNode(url, dir_name, self.secret) 
        thread = Thread(target=node._start)
        thread.setDaemon(1)
        thread.start()
        sleep(HEAD_START)
        self.server = ServerProxy(url)
        for line in open(url_file):
            self.server.hello(line.strip())
        super(Client, self).__init__()  # 将Clint类的对象转换为超类的对象，能够运行OnInit()方法。

    def OnInit(self):  # 重写超类初始化界面的方法
        window = wx.Frame(None, title='P2P文件共享系统', size=(400, 200))  # 创建程序主窗口
        background = wx.Panel(window)  # 创建功能面板
        self.user_input = user_input = wx.TextCtrl(background)  # 添加文本框控件

        submit = wx.Button(background, label='下载', size=(80, 25))  # 添加下载按钮控件
        submit.Bind(wx.EVT_BUTTON, self.fetchHandler)  # 绑定下载事件处理方法
        # submit.Bind(wx.EVT_BUTTON, self.update_list_event)  # 绑定下载事件处理方法

        hbox = wx.BoxSizer()  # 创建尺寸器
        hbox.Add(user_input, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)  # 水平容器中添加文本框
        hbox.Add(submit, flag=wx.TOP | wx.BOTTOM | wx.RIGHT, border=10)  # 水平容器中添加下载按钮

        self.files = files = wx.ListBox(background)  # 添加列表控件
        files.Bind(wx.EVT_LISTBOX_DCLICK, self.dclickItemHandler)  # 绑定列表项点击事件处理方法
        self.update_list()  # 更新文件列表

        vbox = wx.BoxSizer(wx.VERTICAL)  # 创建垂直容器
        vbox.Add(hbox, proportion=0, flag=wx.EXPAND)  # 将水平容器添加到垂直容器
        vbox.Add(files, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.BOTTOM | wx.RIGHT, border=10) # 添加列表控件到垂直容器

        background.SetSizer(vbox)  # 将垂直容器添加到尺寸器
        window.Show()  # 显示程序窗口
        return True

    def dclickItemHandler(self, event):  # 定义列表项点击事件的处理方法
        file_path = os.path.abspath('%s/%s' % (self.dir_name, self.files.GetStringSelection()))  # 获取文件绝对路径
        # os.open(file_path,os.O_RDWR)  # 打开文件
        subprocess.call(["open", file_path])

    def update_list(self):  # 定义更新文件列表的方法
        self.files.Set(self.server.file_list())  # 设置列表控件内容为文件列表
    
    def update_list_event(self, event):  # 定义更新文件列表的方法
        self.update_list()  # 设置列表控件内容为文件列表

    def fetchHandler(self, event):  # 定义下载事件的处理方法
        filename = self.user_input.GetValue()
        try:
            self.server.fetch(filename, self.secret)
            self.update_list()  # 下载后更新文件列表
        except Fault as f:
            if f.faultCode != UNHANDLED:
                raise
            print('没有找到文件：', filename)


def main():  # 定义主程序函数
    url_file, dir_name, url = sys.argv[1:]
    client = Client(url_file, dir_name, url)
    client.MainLoop()

if __name__ == '__main__':
    main()