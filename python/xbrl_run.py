import os
import time
from pathlib import Path
import multiprocessing

from multiprocessing import Process, Array

start_time = time.time()

root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'
report_path = root_dir + '/data/EDINET/四半期報告書'

public_doc_list = []
for category_dir in Path(report_path).glob("*"):
    category_name = os.path.basename(str(category_dir))

    for public_doc in category_dir.glob("*/*/XBRL/PublicDoc"):
        public_doc_list.append( [category_name, public_doc] )

def f(cpu_count, cpu_id, public_doc_list, progress):
    from xbrl_reader import readXbrlThread

    readXbrlThread(cpu_count, cpu_id, public_doc_list, progress)

if __name__ == '__main__':

    cpu_count = multiprocessing.cpu_count()
    progress = Array('i', [0] * cpu_count)

    process_list = []
    for cpu_id in range(cpu_count):

        p = Process(target=f, args=(cpu_count, cpu_id, public_doc_list, progress))

        process_list.append(p)

        p.start()


    for p in process_list:
        p.join()    

    print('終了:%d' % int(time.time() - start_time) )
