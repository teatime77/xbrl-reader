# 出力する項目の指定

<font color="red">ここで書かれている内容はsummary.pyを実行するときコマンドライン引数に'fix'を指定したときのみ有効です。</font>

<font color="red">引数がない場合は、出力する項目は出現頻度によって自動的に決まります。</font>


**summary.py** でCSVファイルに出力する項目は **python** フォルダーの **xbrl_table.py** で指定します。

コンテストごとに出力先のCSVファイルが変わります。

```eval_rst
======================  ===================================
出力先のCSVファイル       コンテスト
======================  ===================================
**summary-0.csv**       提出日時点
**summary-1.csv**       会計終了時点
**summary-2.csv**       会計期間
======================  ===================================
```

以下は、xbrl_table.pyの記述の抜粋です。

```py
filing_date_account_ids = [
    "jpcrp_cor:FilingDateCoverPage", # 提出日 提出日、表紙 dateItemType
    "jpdei_cor:SecurityCodeDEI", # 証券コード 証券コード、DEI stringItemType
]

instant_account_ids = [
    "jppfs_cor:Assets",  # 資産 monetaryItemType
    "jppfs_cor:Liabilities", # 負債 monetaryItemType
]

duration_account_ids = [
    "jppfs_cor:NetSales", # 売上高 売上高 monetaryItemType
    "jppfs_cor:CostOfSales", # 売上原価 売上原価 monetaryItemType
]
```

**summary-0.csv** (提出日時点)に出力する項目は **filing_date_account_ids** の中に書きます。

**summary-1.csv** (会計終了時点)に出力する項目は **instant_account_ids** の中に書きます。

**summary-2.csv** (会計期間)に出力する項目は **duration_account_ids** の中に書きます。

出力する項目を追加したい場合は、 [項目の出現回数](freq_stats.md) で説明した **python/data/stats.txt** の中の1行をコピーして追加してください。
