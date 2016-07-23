from ftplib import FTP
import traceback
import socket
import ConfigParser
import os
import sys
import re

SUCCESS= 0
FAIL   = -1
def debug_print(msg):
    print(msg)

def regformat(filter_type): 
    type_list = filter_type.split(',')
    reg_list  = [''.join(['(\w)',x,'$']) for x in type_list]
    return '|'.join(reg_list)

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
        self.ftp        =  FTP()
        self.load_cfg()

    def load_cfg(self):
        res =           parse_ini('ftpc.ini')
        if res is None:
            debug_print("parse ini fail.Quit.")
            sys.exit(1)
        try:
            self.timeout    =  float(res['FTP']['conn_timeout'])
            self.host       =  res['Server']['host']
            self.remotdir   =  res['Server']['remote_dir']
            self.hostport   =  int(res['Server']['port'])
            self.is_pasv    =  bool(res['FTP']['is_passive'])
            self.username   =  res['Account']['usrname']
            self.password   =  res['Account']['password']
            self.up_local_dir =res['Upload']['local_dir']
            self.up_file_type =res['Upload']['type']
        except KeyError as e:
            debug_print("Unknow key[{}]".format(e))
            sys.exit(1)

        try:
            self.reg_type = regformat(self.up_file_type)
        except Exception as e:
            self.reg_type = None
            debug_print("error file type,do not filter")

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

    def upload_files(self):
        fail_upload_files = []
        files = self.local_files()
        for each_file in files:
            full_filename = os.path.join(self.up_local_dir,each_file)
            if self.upload_file(full_filename,each_file) != SUCCESS:
                fail_upload_files.append(each_file)

        if len(fail_upload_files) == 0:
            debug_print('Upload Success!!')
        else:
            debug_print('fail upload file=%r'%fail_upload_files)
        return

    def local_files(self):
        reg_filter_files = []
        files = os.listdir(self.up_local_dir)
        if self.reg_type is None:
            return files
        if self.reg_type:
            p = re.compile(self.reg_type)
            for each_file in files:
                match_file_obj = p.search(each_file)
                if match_file_obj:
                    reg_filter_files.append(match_file_obj.group())
        return reg_filter_files

    def is_same_size(self,localfile,remotefile):
        try:
            re_size = self.ftp.size(remotefile)
        except:
            debug_print('get remote %s size fail,upload it.'%remotefile)
            return False
        try:
            lo_size = os.path.getsize(localfile)
        except:
            debug_print('get local %s size fail,upload it.'%localfile)
            return False
        if re_size != lo_size:
            return False
        else:
            return True

    def upload_file(self,localfile,remotefile):
        if self.is_same_size(localfile,remotefile):
            return SUCCESS
        debug_print('Uploading {}'.format(remotefile))
        file_handler = open(localfile,'rb')
        try:
            self.ftp.storbinary('STOR %s' %remotefile,file_handler)
        except Exception as e:
            file_handler.close()
            debug_print('upload {} failed'.format(remotefile))
            return FAIL

        file_handler.close()
        return SUCCESS
    
            
    
