'''
name :  Tedu
date :  2018-11-7
email:  xxx
modules: pymysql
This is a dict project for AID
这是字典的服务器
'''
# 要导入的模块
from socket import *
# 创建 多进程 用os
import os 
# 用于历史记录的时间插入
import time
import pymysql
import sys
# 回收僵尸进程
from threading import Thread

# 定义需要的全局变量
DICT_TEXT = './dict.txt'
HOST = '0.0.0.0'
PORT = 8000
ADDR = (HOST,PORT)

# 处理僵尸进程
def zombie():
    # 在这阻塞等待子进程的退出 处理父进程产生的子进程
    os.wait()

# 流程控制
def main():
    # 创建数据库连接
    db = pymysql.connect(host='localhost',
                     user='root',
                     password='123456',
                     database='dictionary',
                     charset='utf8')

    # 创建套接字
    s = socket()
    s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    s.bind(ADDR)
    s.listen(5)
    # 循环等待客户端连接
    while True:
        try:
            c,addr = s.accept()
            print("Connect from",addr)
        # 关键字异常 服务器退出
        except KeyboardInterrupt:
            s.close()
            sys.exit("服务器退出")
        # 其他异常
        except Exception as e:
            print(e)
            continue 

        # 没有异常 就有客户端连接进来了
        # 创建子进程
        pid = os.fork()
        if pid == 0:
            # 进入子进程
            s.close()
            # 等待接受客户端请求
            do_child(c,db)
        else:
            # 创建失败 或 父进程
            c.close()
            # 每当有一个子进程 父进程就创建一个线程处理僵尸进程
            t = Thread(target=zombie)  
            t.setDaemon(True)
            t.start()            
            continue

# 子进程child 用来处理客户端请求
def do_child(c,db):
    print("创建了子进程")
    # 每一个客户端可以长期的占用服务器
    # 循环接收对应的一个客户端请求
    while True:
        try:
            data = c.recv(128).decode()
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            print(e)
        # 打印getpeername客户端地址
        print(c.getpeername(),":",data)
        
        # 进行判断
        
        # 客户端直接断开control C 得到空数据 或者 收到E
        # or先判断前面的 一真则真
        if (not data) or data[0] == 'E':
            c.close()
            # 退出子进程
            sys.exit()
        
        # 进行注册
        elif data[0] == 'R':
            do_register(c,db,data)
        
        # 进行登录
        elif data[0] == 'L':
            do_login(c,db,data)
        
        # 查词
        elif data[0] == 'Q':
            do_query(c,db,data)
        
        # 历史记录
        elif data[0] == 'H':
            do_hist(c,db,data)

# 登录操作
def do_login(c,db,data):
    print("登录操作")
    l = data.split(' ')
    name = l[1]
    passwd = l[2]
    cursor = db.cursor()

    # 查询sql语句
    sql = "select * from user \
    where name='%s' and password='%s'"%(name,passwd)

    cursor.execute(sql)
    r = cursor.fetchone()

    # 没有找到
    if r == None:
        c.send(b'FALL')
    else:
        print("%s登录成功"%name)
        c.send(b'OK')

# 收到客户端请求 进行注册操作
def do_register(c,db,data):
    print("注册操作")
    # 按空格进行切割
    l = data.split(' ')
    name = l[1]
    passwd = l[2]
    
    # 创建游标对象
    cursor = db.cursor()
    # 查找用户数据库 判断注册的用户是否存在
    sql = "select * from user where name='%s';" % name 
    cursor.execute(sql)
    # fetchone 返回的是一条数据 元组
    r = cursor.fetchone()
    
    # 进行判断
    if r != None:
        c.send(b'EXISTS')
        return

    # 用户不存在插入用户
    sql = "insert into user(name,password) \
    values('%s','%s');" % (name,passwd)
    try:
        cursor.execute(sql)
        db.commit()
        # 插入成功 发送给客户端OK
        c.send(b'OK')
        print(1)
    except Exception as e:
        # 插入失败 
        db.rollback()
        c.send(b'FALL')
        print(e)
    else:
        print("%s注册成功" % name)

# 查找单词
def do_query(c,db,data):
    print("查寻操作")
    l = data.split(' ')
    name = l[1]
    word = l[2]
    cursor = db.cursor()
    
    def insert_history():
        # tm为字符串
        tm = time.ctime()
        # print(tm)
        sql = "insert into hist (name,word,time) \
        values('%s','%s','%s')" % (name,word,tm)
        try:
            cursor.execute(sql)
            db.commit()
        except:
            # 插入失败 回滚
            db.rollback()

    # 文本查询
    try:
        # 打开的'./dict.txt'
        f = open(DICT_TEXT)
    except:
        # 打开失败
        c.send(b'FALL')
        return
    # 循环遍历文档
    for line in f:
        tmp = line.split(' ')[0]
        # 判断tmp是否大于要查的单词 大于没有必要继续查找
        if tmp > word:
            c.send(b'FALL')
            f.close()
            return 
        elif tmp == word:
            c.send(b'OK')
            time.sleep(0.1)
            c.send(line.encode())
            f.close()
            # 找到单词之后 生成历史记录插入到数据库
            insert_history()
            return
    # 当整个文档遍历完之后还没有找到单词 发送FALL
    c.send(b'FALL') 
    f.close()   

# 查找历史记录
def do_hist(c,db,data):
    print('历史记录')
    l = data.split()
    # 得到用户的姓名
    name = l[1]
    # 创建游标对象 对数据库进行操作
    cursor = db.cursor()

    # 在hist表中查找name用户的历史记录
    sql = "select * from hist where name='%s';"%name
    # 执行
    cursor.execute(sql)
    # 查找所有的记录  fetchall查找结果为元组套元组
    r = cursor.fetchall()
    # 没有查到
    if not r:
        c.send(b'FALL')
        return
    # 查找到历史记录
    else:
        c.send(b'OK')

    # 遍历历史记录 i是每一次的记录  name word time
    for i in r:
        # 防止粘包
        time.sleep(0.1)
        msg = "%s    %s    %s"%(i[1],i[2],i[3])
        c.send(msg.encode())
    # 发送结束标志
    time.sleep(0.1)
    c.send(b'##')

if __name__ == '__main__':
    main()