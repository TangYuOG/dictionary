# 字典的客户端

#!/usr/bin/python3 
#coding=utf-8 

from socket import * 
import sys 
# 隐藏密码的输入
import getpass

# 创建网络连接
def main():
    # 从命令行直接传入地址和端口号
    if len(sys.argv) < 3:
        print("argv is error")
        return 
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    s = socket()
    
    try:
        # 连接服务器
        s.connect((HOST,PORT))
    except Exception as e:
        # 连接失败
        print(e)
        return

    # 连接成功 显示一级界面
    while True:
        print('''
            ===========Welcome==========
            -- 1.注册   2.登录    3.退出--
            ============================
            ''')
        
        # 处理是否输入有误
        try:
            cmd = int(input("输入选项:"))
        except KeyboardInterrupt:
            sys.exit('客户端退出')
        except Exception as e:
            # 输入的不是数字时 导致int不能转换
            print("命令错误")
            continue 
        
        # 输入内容不在选项范围内
        if cmd not in [1,2,3]:
            print("请输入正确选项")
            # 清除标准输入
            # sys.stdin.flush()
            continue 
        
        # 进行注册
        elif cmd == 1:
            r = do_register(s)
            if r == 0:
                print("注册成功")
                # login(s,name)  #进入二级界面
            elif r == 1:
                print("用户存在")
            else:
                print("注册失败")
        
        # 进行登录
        elif cmd == 2:
            name = do_login(s)
            if name:
                print("登录成功")
                # 传入用户名 知道哪个用户在登录
                login(s,name)
            else:
                print("用户名或密码不正确")
        # 退出
        elif cmd == 3:
            # 向服务器发送退出信息
            s.send(b'E')
            sys.exit("谢谢使用")

# 进行注册
def do_register(s):
    # 循环用于检验用户输入的是否为规范的注册信息
    # 若不规范 则要重复输入
    while True:
        name = input("User:")
        # 输入密码
        passwd = getpass.getpass()
        # 重复密码
        passwd1 = getpass.getpass('Again:')
        
        # 用户名和密码的要求
        if (' ' in name) or (' ' in passwd):
            print("用户名和密码不许有空格")
            continue 
        if passwd != passwd1:
            print("两次密码不一致")
            continue
        # 用户的注册信息
        msg = 'R {} {}'.format(name,passwd)
        print(msg)
        # 发送请求
        s.send(msg.encode())
        # 等待服务器的回复
        data = s.recv(128).decode()
        if data == 'OK':
            # 注册成功 返回到调用方
            return 0
        elif data == 'EXISTS':
            # 用户存在
            return 1
        else:
            # 注册失败
            return 2

# 登录操作
def do_login(s):
    name = input("User:")
    passwd = getpass.getpass()
    msg = "L {} {}".format(name,passwd)
    # 将登录信息给服务器
    s.send(msg.encode())
    # 得到服务器返回信息
    data = s.recv(128).decode()
    # 进行判断
    if data == 'OK':
        # 登录成功 进入到二级界面
        return name
    # 登录失败 
    else:
        return

# 登录进去的二级界面
def login(s,name):
    while True:
        print('''
            ==========查询界面==========
            1.查词    2.历史记录   3.退出
            ===========================
            ''')
        try:
            cmd = int(input("输入选项:"))
        except Exception as e:
            print("命令错误")
            continue 

        if cmd not in [1,2,3]:
            print("请输入正确选项")
            continue 
        # 查词
        elif cmd == 1:
            do_query(s,name)
        # 历史记录
        elif cmd == 2:
            do_hist(s,name)
        
        # 注销 返回到一级界面
        elif cmd == 3:
            # 结束 login函数 返回到 主界面
            return

# 查词
def do_query(s,name):
    while True:
        word = input('单词:')
        # 输入##表示退出 查词
        if word == '##':
            break
        msg = "Q {} {}".format(name,word)
        # 将查找信息发送给服务器
        s.send(msg.encode())
        # 收到服务器返回信息
        data = s.recv(1024).decode()
        # print(1)
        # 对返回信息进行判断
        if data == 'OK':
            data = s.recv(2048).decode()
            print(data)
        else:
            print("没有查到该单词")

# 历史记录
def do_hist(s,name):
    # 发送请求
    msg = 'H {}'.format(name)
    s.send(msg.encode())
    data = s.recv(128).decode() 
    
    # 如果有历史记录 则循环接收
    if data == 'OK':
        # 没办法确定有多少历史记录 所以要循环接收 
        while True:
            data = s.recv(1024).decode()
            # 以##为历史记录结束标志
            if data == '##':
                break
            print(data)
    else:
        print("没有历史记录")


if __name__ == '__main__':
    main()