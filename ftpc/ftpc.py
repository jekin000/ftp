from ftplib import FTP
import traceback
import socket
import ConfigParser
import os
import sys

def debug_print(msg):
    print(msg)

def parse_ini(ini_file_name):
    res = {}
    try:
        dirname = os.path.dirname(os.path.abspath(__file__))
        ini_file = os.path.join(dirname,ini_file_name)
        config = ConfigParser.SafeConfigParser()
        config.read(ini_file)
    except Exception  as e:
        debug_print('parse ini exception')
        debug_print(traceback.format_exc())
        return None
    
    if len(config.sections()) == 0:
        debug_print('No item in ini file.')
        return None

    for sec in config.sections():
        res[sec] = {}
        for k,v in config.items(sec):
            res[sec][k] = v

    return res

class FtpClient(object):
    def __init__(self):
        res =           parse_ini('ftpc.ini')
        if res is None:
            debug_print("parse ini fail.Quit.")
            sys.exit(1)
        try:
            self.timeout    =  float(res['FTP']['conn_timeout'])
            self.ftp        =  FTP()
            self.host       =  res['Server']['host']
            self.hostport   =  int(res['Server']['port'])
            self.is_pasv    =  bool(res['FTP']['is_passive'])
            self.username   =  res['Account']['usrname']
            self.password   =  res['Account']['password']
            self.remotdir   =  res['Upload']['remote_dir']
        except KeyError as e:
            debug_print("Unknow key[{}]".format(e))
            sys.exit(1)

    def close(self):
        self.ftp.close()

    def login(self):
        try:
            socket.setdefaulttimeout(self.timeout)
            self.ftp.set_pasv(self.is_pasv)
            self.ftp.connect(self.host,self.hostport)
            debug_print('Connect Success!!')

            self.ftp.login(self.username,self.password)
            debug_print('Login Success!!')
            debug_print(self.ftp.getwelcome())

        except Exception:
            debug_print('Can not connect or login to Server.')
            debug_print(traceback.format_exc())
            self.ftp.close()
            return

        try:
            self.ftp.cwd(self.remotdir)
        except Exception as e:
            debug_print('Change Dir Exception')
            debug_print(traceback.format_exc())
            self.ftp.close()
        return
            
    def ls(self):
        try:
            self.ftp.dir()
        except:
            debug_print('Error to list file.')
            self.ftp.close()


    
            
    
