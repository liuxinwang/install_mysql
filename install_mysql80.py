#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import commands
import get_ip
import pymysql.cursors
import time
import getpass

def set_root_pwd():
  v_index = 1
  v_new_password = ''
  while v_index == 1:
    v_new_password = getpass.getpass("请设置root新密码：")
    v_new_password2 = getpass.getpass("请再次输入root新密码：")
    if v_new_password == v_new_password2:
      v_index = 2
    else:
      print("密码不一致。")
  
  return v_new_password

os.system("cd ~")
mysql_download_url = "https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-8.0.16-linux-glibc2.12-x86_64.tar.xz"
mysql_tar_filename = "mysql-8.0.16-linux-glibc2.12-x86_64.tar.xz"
mysql_tar_filename2 = "mysql-8.0.16-linux-glibc2.12-x86_64.tar"
mysql_dirname = "mysql-8.0.16-linux-glibc2.12-x86_64/"
mysql_tar_md5 = "60d18d1b324104c83da33dcd7a989816"
if not os.path.exists(mysql_tar_filename2):
  if not os.path.exists(mysql_tar_filename):
    results = commands.getoutput("wget " + mysql_download_url)
  md5sum = commands.getoutput("md5sum " + mysql_tar_filename)
  if md5sum.split("  ", 1)[0] <> mysql_tar_md5:
    print "md5校验失败了！"
    os._exit()
os.system("mkdir /opt/mysql")
if not os.path.exists(mysql_tar_filename2):
  os.system("xz -d " + mysql_tar_filename)
os.system("tar -xvf " + mysql_tar_filename2 + " -C /opt/mysql/")
os.system("ln -s /opt/mysql/" + mysql_dirname + " /usr/local/mysql")
ldd_res = commands.getoutput("ldd /usr/local/mysql/bin/mysqld")
libaio_name = "libaio.so.1 => not found"
if str(ldd_res).find(libaio_name) > -1:
	os.system("yum install libaio -y")
ldd_res = commands.getoutput("ldd mysql/bin/mysqld")
if str(ldd_res).find(libaio_name) > -1:
        print "ldd 失败了！"
	os._exit()
os.system("groupadd mysql")
os.system("useradd -g mysql -d /usr/local/mysql -s /sbin/nologin -MN mysql")
os.system("chown -R mysql:mysql /usr/local/mysql")
os.system("mkdir -p /data/mysql/mysql3306/{data,tmp,logs}")
os.system("cp my803306.cnf /data/mysql/mysql3306/my803306.cnf")
server_id = get_ip.get_host_ip().split(".")[3] + "3306"
os.system("sed -i s/1003306/" + server_id + "/g `grep 1003306 -rl --include=\"my803306.cnf\" /data/mysql/mysql3306/my803306.cnf`")
os.system("chown -R mysql:mysql /data")
os.system("/usr/local/mysql/bin/mysqld --defaults-file=/data/mysql/mysql3306/my803306.cnf --initialize")
os.system("/usr/local/mysql/bin/mysqld --defaults-file=/data/mysql/mysql3306/my803306.cnf &")
os.system("""echo "export PATH=$PATH:/usr/local/mysql/bin" >>/etc/profile""")
commands.getoutput("source /etc/profile")
v_password =  commands.getoutput("more /data/mysql/mysql3306/data/error.log |grep 'A temporary password' | awk 'NR==1{print $13}'")
print("数据库临时密码为：%s" % v_password)
print("登陆语句：""/usr/local/mysql/bin/mysql -S /tmp/mysql3306.sock -uroot -p")
print("关闭readonly语句：" + "set global super_read_only=0; set global read_only=0;")
print("修改root密码为root示例语句：" + "alter user user() identified by 'root';")
