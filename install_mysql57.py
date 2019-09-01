# -*- coding: UTF-8 -*-

import os
import sys
import configparser
import socket
import subprocess
import logging
import getpass
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_host_ip():
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
  finally:
    s.close()
  return ip

def get_conf_file():
  if len(sys.argv) == 1:
    logger.error('配置文件不存在. 例如：python install_mysql57.py conf.ini')
    sys.exit()
  return sys.argv[1]

def get_conf_file_para(conf_file):
  cf = configparser.ConfigParser()
  cf.read(conf_file)
  mysql_version = cf.get('db', 'mysql_version')
  db_port = cf.get('db', 'port')
  md5_value = cf.get('db', 'md5_value')
  pool_size = cf.get('db', 'pool_size')
  return mysql_version, db_port, md5_value, pool_size

def download_mysql(mysql_version, md5_value):
  mysql_tar_filename \
      = "mysql-%s-linux-glibc2.12-x86_64.tar.gz" % mysql_version
  mysql_download_url \
      = "https://dev.mysql.com/get/Downloads/MySQL-5.7/%s" % mysql_tar_filename

  if not os.path.exists(mysql_tar_filename):
    results = subprocess.getoutput("wget " + mysql_download_url)
  md5sum = subprocess.getoutput("md5sum " + mysql_tar_filename)
  if md5sum.split("  ", 1)[0] != md5_value:
    print("md5checksum is failed.")
    sys.exit()

def unzip_mysql(mysql_version):
  mysql_tar_filename = "mysql-%s-linux-glibc2.12-x86_64.tar.gz" % mysql_version
  create_mysql_dir = "/opt/mysql"
  os.system("mkdir %s" % create_mysql_dir)
  os.system("tar -zxvf " + mysql_tar_filename + " -C %s/" % create_mysql_dir)

def ln_mysql(mysql_version):
  mysql_dir_name = "mysql-%s-linux-glibc2.12-x86_64" % mysql_version
  ln_mysql_dir = "/usr/local/mysql"
  if os.path.exists(ln_mysql_dir):
    logger.error(ln_mysql_dir + ' is exists.')
    sys.exit()
  os.system("ln -s /opt/mysql/%s %s" % (mysql_dir_name, ln_mysql_dir))

def ldd_mysqld():
  ldd_res = subprocess.getoutput("ldd /usr/local/mysql/bin/mysqld")
  libaio_name = "libaio.so.1 => not found"
  if str(ldd_res).find(libaio_name) > -1:
    os.system("yum install libaio -y")
  ldd_res = subprocess.getoutput("ldd /usr/local/mysql/bin/mysqld")
  if str(ldd_res).find("not found") > -1:
    logger.error(ldd_res)
    logger.error("ldd is failed.")
    sys.exit()

def create_user():
  result = subprocess.getoutput("grep ^mysql: /etc/passwd | awk -F: '{print $1}'|head -1")
  if result:
    logger.warning("mysql user is exists")
  else:
    os.system("groupadd mysql")
    os.system("useradd -g mysql -d /usr/local/mysql -s /sbin/nologin -MN mysql")

def dir_definition(db_port):
  data_dir = "/data/mysql/mysql%s" % db_port
  if os.path.exists(data_dir):
    logger.error(data_dir + ' is exists.')
    sys.exit()
  os.system("mkdir -p %s/{data,tmp,logs}" % data_dir)
  os.system("cp my57.cnf %s/my%s.cnf" % (data_dir, db_port))

def copy_cnf(db_port, pool_size):
  server_id = get_host_ip().split(".")[3] + db_port
  os.system("sed -i s/1003306/" + server_id + "/g /data/mysql/mysql%s/my%s.cnf" % (db_port, db_port))
  os.system("sed -i s/3306/%s/g /data/mysql/mysql%s/my%s.cnf" % (db_port, db_port, db_port))
  os.system("sed -i s/4096M/%s/g /data/mysql/mysql%s/my%s.cnf" % (pool_size, db_port, db_port))

def dir_chown():
  os.system("chown -R mysql:mysql /usr/local/mysql/")
  os.system("chown -R mysql:mysql /data/")

def init_mysql(db_port):
  os.system(
      """/usr/local/mysql/bin/mysqld \
      --defaults-file=/data/mysql/mysql%s/my%s.cnf \
      --initialize""" % (db_port, db_port))
  result = subprocess.getoutput(
      "cat /data/mysql/mysql%s/data/error.log | grep ERROR"
      % db_port
  )
  if result:
    logger.error("MySQL initialization failed.")
    logger.error(result)
    sys.exit()

def start_mysqld(db_port):
  result = subprocess.getoutput(
      """/usr/local/mysql/bin/mysqld \
      --defaults-file=/data/mysql/mysql%s/my%s.cnf &"""
      % (db_port, db_port)
  )
  while True:
    result = subprocess.getoutput("ps -eo user,stat | grep mysql | awk '{print $2}'")
    if result:
      if result.find('Sl') == -1:
        logger.info("Waiting for mysqld to start up")
        time.sleep(0.1)
      else:
        time.sleep(3)
        break
    else:
      logger.error("MySQL failed to start.")
      logger.error(result)
      sys.exit()

#def init_PATH():
#  os.environ['PATH'] = '%s:%s' % (os.environ['PATH'], '/usr/local/mysql/bin')
#  print(subprocess.getoutput('echo $PATH'))
#  os._exit()
  #os.system("""echo "export PATH=$PATH:/usr/local/mysql/bin" >>/etc/profile""")
  #print("source /etc/profile")

def exec_mysql_cmd(db_port, password, cmd):
  mysql_path = "/usr/local/mysql/bin/mysql"
  mysql_sock = "/tmp/mysql%s.sock" % db_port
  os.system("""%s -S %s -p'%s' -e "%s" """
      % (mysql_path, mysql_sock, password, cmd))

def exec_mysql_cmd_init_password(db_port, cmd):
  result = subprocess.getoutput(
    """more /data/mysql/mysql%s/data/error.log \
    |grep "A temporary password" """ % db_port
  )
  tmp_password = result.split('root@localhost: ')[1]
  mysql_path = "/usr/local/mysql/bin/mysql"
  mysql_sock = "/tmp/mysql%s.sock" % db_port
  os.system("""%s -S %s -p'%s' -e "%s" --connect-expired-password """
      % (mysql_path, mysql_sock, tmp_password, cmd))

def cancel_readonly(db_port):
  cancel_read_only = "set global super_read_only=0; set global read_only=0;"
  exec_mysql_cmd_init_password(db_port, cancel_read_only)

def modify_init_password(db_port):
  while True:
    new_password1 = getpass.getpass('输入root新密码:')
    new_password2 = getpass.getpass('再次输入root新密码:')
    if new_password1 != new_password2:
      print('两次输入的密码不一致')
    else:
      break
  modify_password = "alter user user() identified by '%s';" % new_password1
  exec_mysql_cmd_init_password(db_port, modify_password)
  return new_password1

def install_plugin(db_port, new_password):
  install_semisync_master = "install plugin rpl_semi_sync_master soname 'semisync_master.so';"
  exec_mysql_cmd(db_port, new_password, install_semisync_master)
  install_semisync_slave = "install plugin rpl_semi_sync_slave soname 'semisync_slave.so';"
  exec_mysql_cmd(db_port, new_password, install_semisync_slave)

def shutdown_mysql(db_port, password):
  os.system(
    """/usr/local/mysql/bin/mysqladmin \
    -S /tmp/mysql%s.sock \
    -p'%s' shutdown """ % (db_port, password)
  )

def modify_my_cnf_para(db_port):
  os.system(
    """sed -i 157,160 s/^#//g /data/mysql/mysql%s/my%s.cnf"""
    % (db_port, db_port))

def login_mysql(db_port, password):
  os.system(
      """/usr/local/mysql/bin/mysql -S /tmp/mysql%s.sock -p'%s' """
      % (db_port, password)
  )

def main():
  try:
    logger.info('start read conf')
    confFile = get_conf_file()
    logger.info('read conf done.')

    logger.info('get conf para')
    mysql_version, db_port, md5_value, pool_size = get_conf_file_para(confFile)
    logger.info('mysql_version: %s db_port: %s md5_value: %s pool_size: %s',
                mysql_version,
                db_port,
                md5_value,
                pool_size)

    logger.info('start download mysql')
    download_mysql(mysql_version, md5_value)
    logger.info('download mysql done.')

    create_mysql_dir = "/opt/mysql"
    if os.path.exists(create_mysql_dir):
      logger.error(create_mysql_dir + ' is exists.')
      is_ins_multiple_instance = input("是准备安装多实例吗？(y/n)")
      if is_ins_multiple_instance.lower() == 'n':
        sys.exit()
      elif is_ins_multiple_instance.lower() == 'y':
        logger.warning('jump unzip mysql')
        logger.warning('jump ln mysql')
        logger.warning('jump ldd mysqld')
        logger.warning('jump create mysql user')
    else:
      logger.info('start unzip mysql')
      unzip_mysql(mysql_version)
      logger.info('unzip mysql done.')

      logger.info('start ln mysql')
      ln_mysql(mysql_version)
      logger.info('ln mysql done.')

      logger.info('start ldd mysqld')
      ldd_mysqld()
      logger.info('ldd mysqld done.')

      logger.info('start create mysql user')
      create_user()
      logger.info('create mysql user done.')

    logger.info('create mysql dir')
    dir_definition(db_port)
    logger.info('create mysql dir done')

    logger.info('start copy my.cnf')
    copy_cnf(db_port, pool_size)
    logger.info('copy my.cnf done')

    logger.info('give dir grants')
    dir_chown()
    logger.info('dir grants done')

    logger.info('start init mysql')
    init_mysql(db_port)
    logger.info('mysql init done')

    logger.info('start mysqld')
    start_mysqld(db_port)
    logger.info('mysqld start done')

    # logger.info('init PATH')
    # init_PATH()

    logger.info('cancel mysql read only')
    cancel_readonly(db_port)
    logger.info('cancel mysql read only done')

    logger.info('modiry mysql init password')
    new_password = modify_init_password(db_port)
    logger.info('modify done')

    logger.info('start install plugin')
    install_plugin(db_port, new_password)
    logger.info('install plugin done')

    logger.info('start shutdown mysql')
    shutdown_mysql(db_port, new_password)
    logger.info('shutdown mysql done')

    logger.info('start mysqld')
    start_mysqld(db_port)
    logger.info('mysqld start done')

    logger.info('Log in to the MySQL command line with a new password')
    login_mysql(db_port, new_password)
  except Exception as e:
    print(e)
  except:
    logger.info('异常退出')
  finally:
    logger.info('')

if __name__ == '__main__':
  main()