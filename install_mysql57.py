#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import commands
import get_ip

os.system("cd ~")
mysql_download_url = "https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-5.7.25-linux-glibc2.12-x86_64.tar.gz"
mysql_tar_filename = "mysql-5.7.25-linux-glibc2.12-x86_64.tar.gz"
mysql_dirname = "mysql-5.7.25-linux-glibc2.12-x86_64/"
mysql_tar_md5 = "d241f5dd6527cf1f9ff39449538c1eb1"
if not os.path.exists(mysql_tar_filename):
        results = commands.getoutput("wget " + mysql_download_url)
md5sum = commands.getoutput("md5sum " + mysql_tar_filename)
if md5sum.split("  ", 1)[0] <> mysql_tar_md5:
	print "md5校验失败了！"
	os._exit()
os.system("mkdir /opt/mysql")
os.system("tar -zxvf " + mysql_tar_filename + " -C /opt/mysql/")
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
os.system("chown -R mysql:mysql /usr/local/mysql/")
os.system("mkdir -p /data/mysql/mysql3306/{data,tmp,logs}")
os.system("cp my3306.cnf /data/mysql/mysql3306/my3306.cnf")
server_id = get_ip.get_host_ip().split(".")[3] + "3306"
os.system("sed -i s/1003306/" + server_id + "/g `grep 1003306 -rl --include=\"my3306.cnf\" /data/mysql/mysql3306/my3306.cnf`")
os.system("chown -R mysql:mysql /data")
os.system("/usr/local/mysql/bin/mysqld --defaults-file=/data/mysql/mysql3306/my3306.cnf --initialize")
os.system("/usr/local/mysql/bin/mysqld --defaults-file=/data/mysql/mysql3306/my3306.cnf &")
os.system("""echo "export PATH=$PATH:/usr/local/mysql/bin" >>/etc/profile""")
os.system("source /etc/profile")
print commands.getoutput("more /data/mysql/mysql3306/data/error.log |grep password")
print "set global super_read_only=0; set global read_only=0;"
print "alter user user() identified by 'root';"
os.system("mysql -S /tmp/mysql3306.sock -p")
