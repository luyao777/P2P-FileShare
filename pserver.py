from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy, Fault  # 导入故障异常类Fault
from os.path import isfile, abspath, join  # 导入绝对路径的方法abspath
from urllib.parse import urlparse
from random import choice  # 导入随机选取的方法
from string import ascii_lowercase  # 导入小写字母列表对象
import sys  # 导入系统模块
from fn_recv import socket_service
from fn_send import socket_client
import threading

SimpleXMLRPCServer.allow_reuse_address = 1  # 保证节点服务器重启时能够立即访问
MAX_HISTORY_LENGTH = 6

UNHANDLED = 100  # 文件不存在的异常代码
ACCESS_DENIED = 200  # 文件访问受限的异常代码

def random_string(length):  # 定义随机密钥的函数
    secret = ''
    while length > 0:
        length -= 1
        secret += choice(ascii_lowercase)  # 随机获取小写字母叠加到变量
    return secret

class UnhandledQuery(Fault):  # 创建自定义异常类
    def __init__(self, message='无法处理请求！'):  # 定义构造方法
        Fault.__init__(self, UNHANDLED, message)  # 重载超类构造方法


class AccessDenied(Fault):  # 创建自定义异常类
    def __init__(self, message='访问资源受限！'):  # 定义构造方法
        Fault.__init__(self, ACCESS_DENIED, message)  # 重载超类构造方法


def inside(dir_path, file_path):  # 定义文件路径检查的方法
    directory = abspath(dir_path)  # 获取共享目录的绝对路径
    file = abspath(file_path)  # 获取请求资源的绝对路径
    return file.startswith(join(directory, ''))  # 返回请求资源的路径是否以共享目录路径开始


def get_port(url):
    result = urlparse(url)[1]
    port = result.split(':')[-1]
    return int(port)

def get_addr(url):
    result = urlparse(url)[1]
    addr = result.split(':')[0]
    return addr


class Node:
    def __init__(self, url, dir_name, secret):
        self.url = url
        self.dirname = dir_name
        self.secret = secret
        self.known = set()

    def _start(self):
        server = SimpleXMLRPCServer(('', get_port(self.url)), logRequests=False)
        server.register_instance(self)
        server.serve_forever()

    def _handle(self, source_url, filename):
        print('handle')
        file_path = join(self.dirname, filename)
        if not isfile(file_path):  # 如果路径不是一个文件
            print('unhanded query')
            raise UnhandledQuery  # 抛出文件不存在的异常
        if not inside(self.dirname, file_path):  # 如果请求的资源不是共享目录中的资源
            print('access denied')
            raise AccessDenied  # 抛出访问资源受限异常
        print('_handle success')
        # return 'ok'
        ###########
        # socket_service(get_addr(self.url), get_port(self.url), self.dirname) 
        print('request << ' + source_url)
        send = threading.Thread(target=socket_client, args=(get_addr(source_url), get_port(source_url)+10000, file_path))
        send.start()
        ###########
        # return open(file_path,'r').read()  # 未发生异常时返回读取的文件数据
        return 'ok'

    def _broadcast(self, source_url, filename, history):
        print('broadcast')
        for other in self.known.copy():
            print(other)
            if other in history:
                continue
            try:
                print('broadcast >> ' + other)
                server = ServerProxy(other)
                return server.query(source_url, filename, history)
                
            except Fault as f:  # 如果捕获访问故障异常获取异常代码
                print('fault')
                if f.faultCode == UNHANDLED:  # 如果是文件不存在异常
                    print('fault none file')
                    continue  # 不做任何处理
                else:  # 如果是其它故障异常
                    print('fault other error')
                    self.known.remove(other)  # 从已知节点列表中移除节点
            except:  # 如果捕获其它异常（非故障异常）
                self.known.remove(other)  # 从已知节点列表中移除节点
        raise UnhandledQuery  # 如果已知节点都未能请求到资源，抛出文件不存在异常。

    def query(self, source_url, filename, history=[]):
        try:
            print('query')
            return self._handle(source_url, filename)
        except UnhandledQuery:  # 如果捕获文件不存在的异常
            print('query unhandled')
            history.append(self.url)
            if len(history) >= MAX_HISTORY_LENGTH:
                raise
            return self._broadcast(source_url, filename, history)

    def hello(self, other):
        self.known.add(other)
        return 0  # 必须返回非None的值

    def fetch(self, filename, secret):
        if secret != self.secret:  # 如果密钥不匹配
            print('key error')
            raise AccessDenied  # 抛出访问资源受限异常
        recv = threading.Thread(target=socket_service, args=(get_addr(self.url), get_port(self.url)+10000, self.dirname))
        recv.start()
        result = self.query(self.url, filename)
        print(result)
        # with open(join(self.dirname, filename), 'w') as file:
        #     file.write(result)
        return 0  # 必须返回非None的值


def main():  # 定义主程序函数，用于测试当前代码是否正常。
    url, directory, secret = sys.argv[1:]  # 获取通过命令行终端输入参数
    node = Node(url, directory, secret)  # 创建节点对象
    node._start()  # 启动节点服务器


if __name__ == '__main__':
    main()  # 运行主程序
