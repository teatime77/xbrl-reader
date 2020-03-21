# 実行手順


## 処理の概要

以下の４つの処理があります。

* **処理１** : 金融庁の[EDINET](https://disclosure.edinet-fsa.go.jp/)からZIPファイルをダウンロードします。
* **処理２** : ZIPファイルの中からXBRLインスタンスファイルを抽出します。
* **処理３** : XBRLインスタンスファイルから **summary-0.csv**, **summary-1.csv**, **summary-2.csv** を作ります。
* **処理４** : **summary-0.csv**, **summary-1.csv**, **summary-2.csv** と会社情報から **summary-join.csv** を作ります。

**処理１** は３日くらいかかり、ダウンロードしたファイルは13GBくらいになります。  
  
**処理３** と **処理４** はGoogle Colaboratory でも実行できます。  
処理内容は以下の Jupyter ノートブックをご覧ください。  
* [処理３のノートブック](https://github.com/teatime77/xbrl-reader/blob/master/notebook/make_summary_012.ipynb)  
* [処理４のノートブック](https://github.com/teatime77/xbrl-reader/blob/master/notebook/make_summary_join.ipynb)  
  
**処理１** と **処理２** は省略して、 **処理２** で作ったデータを使って **処理３** 以降を実行することもできます。  
  
以下では **処理１** と **処理２** の実行手順を説明します。  

## 動作環境設定

**Windows10** で **python 3.7** を使いました。

#### 1. pythonのライブラリをインストールします。

XHTMLをパースするのに **lxml** を使っています。  
[lxml - XML and HTML with Python](https://lxml.de/)  
  
pipでインストールできます。

```bash
pip install lxml
```

※ pythonで使う外部ライブラリは **lxml** だけです。

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

## 処理１． 金融庁のEDINETからZIPファイルをダウンロードします。

**python** フォルダーに移動して **download.py** を実行します。

```bash
cd XBRL-HOME/python
python download.py
```

全上場企業の過去５年分の有価証券報告書、四半期報告書、半期報告書をダウンロードします。  
ダウンロードしたZIPファイルは **XBRL-HOME/zip/download** の日付別のフォルダーに入ります。  
  
全部ダウンロードするのに３日以上かかります。  
途中でエラーになった場合は、再度download.pyを実行するとエラーになったところからダウンロードを再開します。

## 処理２． ZIPファイルの中からXBRLインスタンスファイルを抽出します。

**python** フォルダーで以下を実行します。

```bash
python extract.py
```

会社ごとにXBRLインスタンスファイルをまとめたZIPファイルが **XBRL-HOME/zip/extract** に入ります。  
サイズは5GBくらいです。  
  
これをtarで8つにまとめたファイルが以下にあります。  
* [http://lkzf.info/xbrl/data/extract/extract-0.tar](http://lkzf.info/xbrl/data/extract/extract-0.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-1.tar](http://lkzf.info/xbrl/data/extract/extract-1.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-2.tar](http://lkzf.info/xbrl/data/extract/extract-2.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-3.tar](http://lkzf.info/xbrl/data/extract/extract-3.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-4.tar](http://lkzf.info/xbrl/data/extract/extract-4.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-5.tar](http://lkzf.info/xbrl/data/extract/extract-5.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-6.tar](http://lkzf.info/xbrl/data/extract/extract-6.tar)  
* [http://lkzf.info/xbrl/data/extract/extract-7.tar](http://lkzf.info/xbrl/data/extract/extract-7.tar)  

**処理３** はこのデータを使います。