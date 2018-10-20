import os
import time
import re
from pathlib import Path
import multiprocessing

from multiprocessing import Process, Array

start_time = time.time()

root_dir = os.path.dirname( os.path.abspath(__file__) ).replace('\\', '/') + '/..'
report_path = root_dir + '/data/EDINET/四半期報告書'

def make_public_docs_list(cpu_count):
    public_docs_list = [ [] for i in range(cpu_count) ]
    for category_dir in Path(report_path).glob("*"):
        category_name = os.path.basename(str(category_dir))

        for public_doc in category_dir.glob("*/*/XBRL/PublicDoc"):
            xbrl_path_list = list(public_doc.glob('jpcrp*.xbrl'))
            assert len(xbrl_path_list) == 1

            xbrl_path = xbrl_path_list[0]
            xbrl_basename = os.path.basename(str(xbrl_path))
            items = re.split('[-_]', xbrl_basename)
            edinet_code = items[3]
            char_sum = sum(ord(x) for x in edinet_code)
            cpu_idx  = char_sum % cpu_count

            public_docs_list[cpu_idx].append( [category_name, public_doc] )

    return public_docs_list

def f(cpu_count, cpu_id, public_docs_list, progress):
    from xbrl_reader import readXbrlThread

    readXbrlThread(cpu_count, cpu_id, public_docs_list, progress)

if __name__ == '__main__':

    cpu_count = multiprocessing.cpu_count()
    # cpu_count = 1
    # cpu_id = 0
    progress = Array('i', [0] * cpu_count)
    # f(cpu_count, cpu_id, public_docs_list, progress)

    public_docs_list = make_public_docs_list(cpu_count)

    process_list = []
    for cpu_id in range(cpu_count):

        print('run cpu:%d cnt:%d' % (cpu_id, len(public_docs_list[cpu_id])))
        p = Process(target=f, args=(cpu_count, cpu_id, public_docs_list[cpu_id], progress))

        process_list.append(p)

        p.start()


    for p in process_list:
        p.join()    

    print('終了:%d' % int(time.time() - start_time) )
