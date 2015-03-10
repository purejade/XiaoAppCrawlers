__author__ = 'purejade'
import os
import codecs

ROOT_DIR = 'G:'+os.sep+'FtpDir'+os.sep+'NEW_XIAO_APPS'+os.sep
finished_handler = codecs.open(ROOT_DIR+'finished_app_id','a+','utf-8')

new_finished_handler = codecs.open(ROOT_DIR+'new_finished_app_id','a+','utf-8')

for line in finished_handler:
    line = line.strip()
    if line:
        if len(line) <= 5:
            new_finished_handler.write(line)
            new_finished_handler.write(os.linesep)
        if len(line) == 10:
            new_finished_handler.write(line[0:5])
            new_finished_handler.write(os.linesep)
            new_finished_handler.write(line[5:])
            new_finished_handler.write(os.linesep)
        if len(line) > 5 and len(line) != 10:
            print line

