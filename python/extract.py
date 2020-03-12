import os
import zipfile
from pathlib import Path
import re
import codecs
import multiprocessing
from multiprocessing import Process

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path = root_dir + '/python/data'
download_path = root_dir + '/zip/download'
extract_path = root_dir + '/zip/extract'

def get_zip_dic():
    dic = {}
    for zip_path_obj in Path(download_path).glob("**/*.zip"):
        zip_path = str(zip_path_obj)
        edinetCode = os.path.basename(zip_path).split('-')[0]
        if edinetCode in dic:
            dic[edinetCode].append(zip_path)
        else:
            dic[edinetCode] = [ zip_path ]

    return dic

def group_zip(cpu_count, cpu_id, dic):
    xbrl = re.compile('XBRL/PublicDoc/jpcrp[-_0-9a-zA-Z]+\.xbrl')

    log_f = codecs.open("%s/group_log.txt" % data_path, 'w', 'utf-8')

    for edinetCode, zip_paths in dic.items():
        assert edinetCode[0] == 'E'        
        if int(edinetCode[1:]) % cpu_count != cpu_id:
            continue

        extract_sub_path = '%s/%s' % (extract_path, cpu_id)
        if not os.path.exists(extract_sub_path):
            # フォルダーがなければ作る。

            os.makedirs(extract_sub_path)


        group_zip_path = "%s/%s.zip" % (extract_sub_path, edinetCode)
        print(group_zip_path)
        with zipfile.ZipFile(group_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
            for zip_path in zip_paths:
                try:
                    with zipfile.ZipFile(zip_path) as zf:
                        for xbrl_file in [x for x in zf.namelist() if xbrl.match(x)]:
                            with zf.open(xbrl_file) as f:
                                xml_bin = f.read()

                            file_name = xbrl_file.split('/')[-1]
                            new_zip.writestr(file_name, xml_bin)

                            break

                except zipfile.BadZipFile:
                    print("\nBadZipFile : %s\n" % zip_path)
                    log_f.write("BadZipFile:[%s]\n" % zip_path)
                    continue

    log_f.close()

if __name__ == '__main__':
    dic = get_zip_dic()

    cpu_count = multiprocessing.cpu_count()
    process_list = []
    for cpu_id in range(cpu_count):

        p = Process(target=group_zip, args=(cpu_count, cpu_id, dic))

        process_list.append(p)

        p.start()

    for p in process_list:
        p.join()
