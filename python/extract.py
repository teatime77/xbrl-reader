import os
import zipfile
from pathlib import Path
import re
import codecs

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
data_path = root_dir + '/python/data'
docs_path = root_dir + '/xbrl-zip'
group_path = root_dir + '/group-zip'

def group_zip():
    dic = {}
    for zip_path_obj in Path(docs_path).glob("**/*.zip"):
        zip_path = str(zip_path_obj)
        edinetCode = os.path.basename(zip_path).split('-')[0]
        if edinetCode in dic:
            dic[edinetCode].append(zip_path)
        else:
            dic[edinetCode] = [ zip_path ]

    if not os.path.exists(group_path):
        # フォルダーがなければ作る。

        os.makedirs(group_path)

    xbrl = re.compile('XBRL/PublicDoc/jpcrp[-_0-9a-zA-Z]+\.xbrl')

    log_f = codecs.open("%s/group_log.txt" % data_path, 'w', 'utf-8')

    for edinetCode, zip_paths in dic.items():
        group_zip_path = "%s/%s.zip" % (group_path, edinetCode)
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
    group_zip()
