# 実行手順

## 動作環境設定

**Windows10** で **python 3.7** を使いました。

#### 1. pythonのライブラリをインストールします。

XHTMLをパースするのに **lxml** を使い、CSVファイルの処理に **pandas** を使っています。  

 **lxml** も **pandas** もpipでインストールできます。

```bash
pip install lxml
pip install pandas
```

#### 2. ソースをダウンロードします。

適当なフォルダーにgitでcloneします。

```bash
git clone https://github.com/teatime77/xbrl-reader.git
```

以下では **XBRL-HOME** というフォルダーにダウンロードしたとして説明します。

### 3. タクソノミファイルを取得します。

以下のURLからEDINETのタクソノミが入ったファイルをダウンロードして解凍します。  
[http://lkzf.info/xbrl/data/data-2019-11-01.zip](http://lkzf.info/xbrl/data/data-2019-11-01.zip)  
  
解凍した **data** フォルダーを **XBRL-HOME** の直下に入れます。  
以下のようなフォルダー構成になります。

```bash
XBRL-HOME - python
          - docs
          - web
          - data - EDINET - taxonomy
                          - EdinetcodeDlInfo.csv
```

## ZIPファイルをダウンロード

**python** フォルダーに移動して **download.py** を実行します。

```bash
cd XBRL-HOME/python
python download.py
```

金融庁の[EDINET](https://disclosure.edinet-fsa.go.jp/)から全上場企業の過去５年分の有価証券報告書、四半期報告書、半期報告書のZIPファイルをダウンロードします。  

ダウンロードしたZIPファイルは **XBRL-HOME/zip/download** の日付別のフォルダーに入ります。  
  
全部ダウンロードするのに３日くらいかかり、ファイルサイズは13GBくらいになります。 

途中でエラーになった場合は、再度download.pyを実行するとエラーになったところからダウンロードを再開します。

## XBRLインスタンスを抽出
ZIPファイルの中からXBRLインスタンスファイルを抽出します。

**python** フォルダーで以下を実行します。

```bash
python extract.py
```

会社ごとにXBRLインスタンスファイルをまとめたZIPファイルが **XBRL-HOME/zip/extract** に入ります。  
サイズは5GBくらいです。  
  
これをtarで8つにまとめたファイルが以下にあります。  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-0.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-0.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-1.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-1.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-2.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-2.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-3.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-3.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-4.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-4.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-5.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-5.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-6.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-6.tar)  
* [http://lkzf.info/xbrl/data/2020-04-08/extract/extract-7.tar](http://lkzf.info/xbrl/data/2020-04-08/extract/extract-7.tar)  

## XBRL→CSV作成

**python** フォルダーで以下のように引数に **fix** をつけて **summary.py** を実行します。

```bash
python summary.py fix
```

実行すると **python/data** フォルダーに以下のファイルが作られます。

```eval_rst
======================  ===================================
ファイル名               内容
======================  ===================================
**summary-0.csv**       報告書の提出日 **時点** の情報  
**summary-1.csv**       会計終了 **時点** の情報  
**summary-2.csv**       会計 **期間** の情報  
**stats.json**          各項目の出現頻度
======================  ===================================
```

引数に **fix** をつけると、出力する項目は **xbrl_table.py** で指定した項目になります。  
 ( [出力する項目の指定](output_items.md) )


出力する項目を出現頻度によって自動的に決めたい場合は以下の手順をします。

1. 最初に引数に **fix** をつけて **summary.py** を実行します。
2. **python/data** フォルダーに作られた項目ごとの出現頻度のファイル( **stats.json** )を、 **stats-master.json** にリネームします。
3. 引数をつけずに **summary.py** を実行します。

出力する項目を手動で指定したい場合は **fix** をつけ、出力項目を自動的に絞り込みたい場合は **fix** をつけません。

## 表を結合

**summary-0.csv**, **summary-1.csv**, **summary-3.csv** を結合して１つの表にします。

**python** フォルダーで以下を実行します。

```bash
python join.py
```

結合した表は **python/data** フォルダーに **summary-join.csv** というCSVファイルに保存されます。


## 業績予想の前処理, 業績予想

これらの処理はGoogle Colaboratory でも実行できます。  
処理内容は以下の Jupyter ノートブックをご覧ください。  

* [業績予想の前処理](https://github.com/teatime77/xbrl-reader/blob/master/notebook/preprocess.ipynb)  
* [業績予想(sklearn)](https://github.com/teatime77/xbrl-reader/blob/master/notebook/sklearn.ipynb)  
* [業績予想(TensorFlow)](https://github.com/teatime77/xbrl-reader/blob/master/notebook/TensorFlow.ipynb)  
