#!/usr/bin/env python
# -*- coding=utf-8 -*-


import socket
import threading
import time
import sys
import os
import struct


def socket_service(own_addr, own_port, dir_path):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((own_addr, own_port))
        s.listen(10)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('Waiting connection...')

    while 1:
        conn, addr = s.accept()
        t = threading.Thread(target=deal_data, args=(conn, addr, dir_path))
        t.start()

def deal_data(conn, addr, dir_path):
    print('Accept new connection from {0}'.format(addr))
    #conn.settimeout(500)
    conn.send(b'Hi, Welcome to the server!')

    while 1:
        fileinfo_size = struct.calcsize('128sl')
        buf = conn.recv(fileinfo_size)
        if buf:
            filename, filesize = struct.unpack('128sl', buf)
            fn = str(filename.strip(bytes('\00'.encode('utf-8'))))[2:-1]
            new_filename = os.path.join(dir_path,fn)
            print('file new name is {0}, filesize if {1}'.format(new_filename,
                                                                 filesize))

            recvd_size = 0  
            fp = open(new_filename, 'wb')
            print('start receiving...')

            while not recvd_size == filesize:
                if filesize - recvd_size > 1024:
                    data = conn.recv(1024)
                    recvd_size += len(data)
                else:
                    data = conn.recv(filesize - recvd_size)
                    recvd_size = filesize
                fp.write(data)
            fp.close()
            print('end receive...')
        conn.close()
        break


if __name__ == '__main__':
    socket_service()
