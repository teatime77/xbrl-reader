import datetime
import sys
import os
import json
import urllib.request
import codecs
import zipfile
import time

from xbrl_reader import read_company_dic

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
download_path = root_dir + '/zip/download'
data_path = root_dir + '/python/data'

for path in [data_path, download_path]:
    if not os.path.exists(path):
        # フォルダーがなければ作る。

        os.makedirs(path)

# 会社情報の辞書を得る。
company_dic = read_company_dic()

def receive_edinet_doc_list(day_path: str, yyyymmdd: str):
    """EDINETから書類一覧APIを使って書類一覧が入ったJSONオブジェクト取得して返す。

        Args:
            day_path (str): JSONオブジェクトを保存するフォルダーのパス
            yyyymmdd (str): 日付の文字列

        Returns:
            書類一覧が入ったJSONオブジェクト
    """
    # 書類一覧APIのリクエストを送る。
    url = 'https://disclosure.edinet-fsa.go.jp/api/v1/documents.json?date=%s&type=2' % yyyymmdd
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        try:
            body = json.load(res)
        except json.decoder.JSONDecodeError:
            print("書類一覧のデータが不正です。\nEDINETがメンテナンス中の可能性があります。")
            sys.exit()

    if body['metadata']['status'] == "404":
        # 書類がない場合

        print("報告書の取得を終了しました。")
        return None

    assert body['metadata']['message'] == "OK"

    # JSONをファイルに書く。
    json_path = "%s/docs.json" % day_path
    with codecs.open(json_path, 'w', 'utf-8') as json_f:
        json.dump(body, json_f, ensure_ascii=False)

    return body

def check_zip_file(zip_path: str):
    """ZIPファイルが壊れていないか調べる。

    Args:
        zip_path(str): ZIPファイルのパス

    Returns:
        bool: 壊れていなければTrue
    """
    try:
        # ZIPファイルを開いて壊れていないか調べる。
        with zipfile.ZipFile(zip_path) as zf:
            file_list = list(zf.namelist())

        return True
    except zipfile.BadZipFile:
        return False

def receive_edinet_doc(doc, dst_path):
    """EDINETから書類取得APIで決算情報のZIPファイルをダウンロードする。

    Args:
        doc          : 書類オブジェクト
        dst_path(str): ダウンロード先のパス
    """
    edinetCode = doc['edinetCode']
    company = company_dic[edinetCode]

    # 提出日時、提出者名、提出書類概要、業種を画面表示する。
    print("%s | %s | %s | %s" % (doc['submitDateTime'], doc['filerName'], doc['docDescription'], company['category_name_jp']))

    # 書類取得APIのリクエストを送る。
    url = "https://disclosure.edinet-fsa.go.jp/api/v1/documents/%s?type=1" % doc['docID']
    with urllib.request.urlopen(url) as web_file:
        data = web_file.read()

        # 決算情報のZIPファイルに書く。
        with open(dst_path, mode='wb') as local_file:
            local_file.write(data)

        if not check_zip_file(dst_path):
            # ZIPファイルが壊れている場合

            print("!!!!!!!!!! ERROR !!!!!!!!!!\n" * 1)
            print("msg:[%s] status:[%s] reason:[%s]" % (str(web_file.msg), str(web_file.status), str(web_file.reason) ))
            print("!!!!!!!!!! ERROR [%s] !!!!!!!!!!\n" % dst_path)
            print(json.dumps(doc, indent=2, ensure_ascii=False))
            print("!!!!!!!!!! ERROR !!!!!!!!!!\n" * 1)

            os.remove(dst_path)
            time.sleep(2)

    time.sleep(1)

def select_doc(day_path, body):
    """書類一覧の中で対象となる書類を返す。

    対象となる書類とは以下の条件を満たす書類。  

    * 有価証券報告書/四半期報告書/半期報告書またはそれの訂正書類。
    * 財務局職員が修正した書類ではない。  
    * 会社情報の一覧に含まれる上場企業の書類

    Returns:
        対象書類
    """
    for doc in body['results']:   
        docTypeCode = doc['docTypeCode']
        if docTypeCode in [ '120', '130', '140', '150', '160', '170' ] and doc['docInfoEditStatus'] == "0":
            # 有価証券報告書/四半期報告書/半期報告書またはそれの訂正書類で、財務局職員が修正したのではない場合

            edinetCode = doc['edinetCode']
            if edinetCode in company_dic:
                # 会社情報の一覧に含まれる場合

                company = company_dic[edinetCode]
                if company['listing'] == '上場':
                    # 上場企業の場合

                    yield doc

def get_xbrl_docs():
    """ダウンロードのメイン処理

    現在の日付から１日ずつ過去にさかのぼって書類をダウンロードする。
    """

    # 現在の日付
    dt1 = datetime.datetime.today()
    
    while True:
        # １日過去にさかのぼる。
        dt1 = dt1 + datetime.timedelta(days=-1)
            
        yyyymmdd = "%d-%02d-%02d" % (dt1.year, dt1.month, dt1.day)
        print(yyyymmdd)

        day_path = "%s/%d/%02d/%02d" % (download_path, dt1.year, dt1.month, dt1.day)
        if not os.path.exists(day_path):
            # フォルダーがなければ作る。

            os.makedirs(day_path)

        os.chdir(day_path)

        json_path = "%s/docs.json" % day_path
        if os.path.exists(json_path):
            # 書類一覧のJSONファイルがすでにある場合

            with codecs.open(json_path, 'r', 'utf-8') as f:
                body = json.load(f)

        else:
            # 書類一覧のJSONファイルがない場合

            body = receive_edinet_doc_list(day_path, yyyymmdd)
            if body is None:
                break
            time.sleep(1)

        for doc in select_doc(day_path, body):
            dst_path = "%s/%s-%s-%d.zip" % (day_path, doc['edinetCode'], doc['docTypeCode'], doc['seqNumber'])
            if os.path.exists(dst_path):
                # すでに決算情報のZIPファイルがある場合

                if check_zip_file(dst_path):
                    # ZIPファイルが壊れていない場合

                    continue

                # 壊れているZIPファイルは削除する。
                os.remove(dst_path)
                
            # EDINETから決算情報のZIPファイルをダウンロードする。
            receive_edinet_doc(doc, dst_path)


if __name__ == '__main__':
    get_xbrl_docs()
