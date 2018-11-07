# 插入单词到数据库

import pymysql 
import re  

# 打开存单词的文件
try:
    f = open('dict.txt')
    try:
        # 1.连接数据库
        db = pymysql.connect\
        ('localhost','root','123456','dict')
        # 2.创建游标
        cursor = db.cursor()

        # 提取每一行的单词信息
        for line in f:
            l = re.split(r'\s+',line)
            word = l[0]
            interpret = ' '.join(l[1:])
            
            sql = "insert into words (word,interpret) \
            values('%s','%s')"%(word,interpret)

            try:
                cursor.execute(sql)
                db.commit()
            except:
                db.rollback()
    finally:
        f.close()

except Exception as e:
    print('打开失败',e)
