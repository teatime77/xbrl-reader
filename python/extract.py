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
    """EDINETコードとダウンロードしたZIPファイルのリストの辞書を返す。

    * 辞書のキー : EDINETコード
    * 辞書の値   : ダウンロードしたZIPファイルのリスト

    Returns:
        辞書
    """
    dic = {}

    # ダウンロードのフォルダーにあるすべてのZIPファイルに対し
    for zip_path_obj in Path(download_path).glob("**/*.zip"):
        zip_path = str(zip_path_obj)

        # EDINETコードをファイル名から得る。
        edinetCode = os.path.basename(zip_path).split('-')[0]

        if edinetCode in dic:
            # EDINETコードが辞書にある場合

            dic[edinetCode].append(zip_path)
        else:
            # EDINETコードが辞書にない場合

            dic[edinetCode] = [ zip_path ]

    return dic

def group_zip(cpu_count, cpu_id, dic):
    """CPUごとのサブプロセスの処理

    EDINETコードをCPU数で割った余りがCPU-IDに等しければ処理をする。

    Args:
        cpu_count(int): CPU数
        cpu_id   (int): CPU-ID (0, ..., CPU数 - 1)
        dic           : EDINETコードとダウンロードしたZIPファイルのリストの辞書
    """
    xbrl = re.compile('XBRL/PublicDoc/jpcrp[-_0-9a-zA-Z]+\.xbrl')

    for edinetCode, zip_paths in dic.items():
        assert edinetCode[0] == 'E'        
        if int(edinetCode[1:]) % cpu_count != cpu_id:
            # EDINETコードをCPU数で割った余りがCPU-IDに等しくない場合

            continue

        extract_sub_path = '%s/%s' % (extract_path, cpu_id)
        if not os.path.exists(extract_sub_path):
            # 抽出先のフォルダーがなければ作る。

            os.makedirs(extract_sub_path)

        # 抽出先のZIPファイルのパス
        extract_zip_path = "%s/%s.zip" % (extract_sub_path, edinetCode)
        print(extract_zip_path)

        # 抽出先のZIPファイルを書き込みモードで開く。
        with zipfile.ZipFile(extract_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:

            # ダウンロードしたZIPファイルのリストに対し
            for zip_path in zip_paths:
                try:
                    # ダウンロードしたZIPファイルを読み取りモードで開く。
                    with zipfile.ZipFile(zip_path) as zf:

                        # ダウンロードしたZIPファイル内のXBRLファイルに対し
                        for xbrl_file in [x for x in zf.namelist() if xbrl.match(x)]:

                            # XBRLファイルのデータを読む。
                            with zf.open(xbrl_file) as f:
                                xml_bin = f.read()

                            # 抽出先のZIPファイルの中にXBRLファイルを書く。
                            file_name = xbrl_file.split('/')[-1]
                            new_zip.writestr(file_name, xml_bin)

                            break

                except zipfile.BadZipFile:
                    print("\nBadZipFile : %s\n" % zip_path)
                    continue

if __name__ == '__main__':
    dic = get_zip_dic()

    cpu_count = multiprocessing.cpu_count()
    process_list = []

    # CPUごとにサブプロセスを作って並列処理をする。
    for cpu_id in range(cpu_count):

        p = Process(target=group_zip, args=(cpu_count, cpu_id, dic))

        process_list.append(p)

        p.start()

    # すべてのサブプロセスが終了するのを待つ。
    for p in process_list:
        p.join()
