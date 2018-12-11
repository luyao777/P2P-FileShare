from xmlrpc.client import ServerProxy, Fault  # 导入服务器代理类和故障类
from random import choice  # 导入随机选取的方法
from string import ascii_lowercase  # 导入小写字母列表对象
from time import sleep  # 导入延迟方法
from pserver import Node, UNHANDLED  # 导入服务器中的节类和变量
from threading import Thread  # 导入线程类
from cmd import Cmd  # 导入命令类
import sys  # 导入系统模块

HEAD_START = 0.1  # 等待服务器启动时长
SECRET_LENGTH = 10  # 密钥长度


def random_string(length):  # 定义随机密钥的函数
    secret = ''
    while length > 0:
        length -= 1
        secret += choice(ascii_lowercase)  # 随机获取小写字母叠加到变量
    return secret


class Client(Cmd):
    prompt = '>>>'  # 重写超类中的命令提示符

    def __init__(self, url_file, dir_name, url):  # 定义构造方法
        Cmd.__init__(self)  # 重载超类的构造方法
        self.secret = random_string(SECRET_LENGTH)  # 创建密钥变量
        node = Node(url, dir_name, self.secret)  # 创建节点对象
        thread = Thread(target=node._start)  # 在独立的线程中启动服务器
        thread.setDaemon(True)  # 将线程设置为守护线程
        thread.start()  # 启动线程
        sleep(HEAD_START)  # 等待服务器启动
        self.server = ServerProxy(url)  # 创建服务器代理对象
        for line in open(url_file):  # 读取URL文件
            self.server.hello(line.strip())  # 添加URL文件中的URL到已知节点集合

    def do_fetch(self, filename):  # 定义下载命令的方法
        try:
            self.server.fetch(filename, self.secret)  # 调用服务器代理对象的下载方法
        except Fault as f:  # 捕获故障异常
            if f.faultCode != UNHANDLED:  # 如果异常代码不是未找到文件
                pass  # 不做处理
            print('找不到文件：', filename)

    def do_exit(self, arg):  # 定义退出命令的方法
        print('------------------退出程序------------------')
        sys.exit()  # 系统退出


def main():  # 定义主程序函数
    urlfile, dir_name, url = sys.argv[1:]  # 获取通过命令行输入的参数
    client = Client(urlfile, dir_name, url)  # 创建客户端对象
    client.cmdloop()  # 启动命令行循环执行


if __name__ == '__main__':
    main()
