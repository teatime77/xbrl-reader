# XBRL Reader

1. XBRLファイルをpythonで解析してJSONに変換します。
2. 変換したJSONをJavascriptで読んでウェブページに表示します。

## 動作環境
以下の環境で動作を確認しています。

### OS
- Windows10
- Ubuntu 16.04

### python
- 3.6

※ python 3.5では型アノテーションの箇所でエラーになりました。

### ウェブブラウザ
- Chrome
- Firefox
- Edge

※ ajaxでローカルファイルを読むので **Chrome** の場合はローカルサーバーが必要です。
※ IEでは動作しません。

## インストール方法

### 1. gitでソースを取得します。

適当なフォルダーにソースをクローンします。

```bash
git clone https://github.com/teatime77/xbrl-reader.git
```

以下では **XBRL-HOME** というフォルダーにクローンしたとして説明します。

### 2. タクソノミファイルを取得します。

以下のURLからEDINETやIFRSのタクソノミが入ったファイルをダウンロードして解凍します。
[http://lang.main.jp/xbrl/data.zip](http://lang.main.jp/xbrl/data.zip)

解凍した **data** フォルダーを **XBRL-HOME** の直下に入れます。
以下のようなフォルダー構成になります。

```bash
XBRL-HOME - python
          - docs
          - web  - report
          - data - EDINET
                 - IFRS                 
```

### 3. サンプルのXBRLデータを取得します。

以下のURLからサンプルのXBRLデータをダウンロード後に解凍して、**XBRL-HOME/web/report** の下に入れます。

[http://lang.main.jp/xbrl/18-12-09.zip](http://lang.main.jp/xbrl/18-12-09.zip)

以下のようなになります。

```bash
XBRL-HOME - python
          - docs
          - web  - report - 18-12-09 - Xbrl_Search_20181209_xxxxxx
                                     - Xbrl_Search_20181209_xxxxxx
                                     - ・・・
          - data - EDINET
                 - IFRS                 
```


### 4. XHTMLのパーサーをインストールします。

XHTMLをパースするのに **lxml** を使っています。
[lxml - XML and HTML with Python](https://lxml.de/)

pipでインストールできます。

```bash
pip install lxml
```

※ pythonで使っているのは **lxml** だけで、それ以外の外部ライブラリは使っていません。

## 実行方法

**python** フォルダーに移動して **xbrl_run.py** を実行します。

```bash
cd XBRL-HOME/python
python xbrl_run.py
```

JSONファイルは **XBRL-HOME/json** に作られます。

JSONファイルは業種ごとに分かれて保存されます。
例えば、電気機器関連は **electronics** フォルダーで、小売業は **retail** フォルダーです。
会社と業種の一覧は **XBRL-HOME/data/EDINET/EdinetcodeDlInfo.csv** にあります。

※ **xbrl_run.py** は同じフォルダーにある **xbrl_reader.py** をマルチプロセスで実行するプログラムです。
デバッグするときは直接 **xbrl_reader.py** をマルチプロセスで実行すると使いやすいです。

```bash
python xbrl_reader.py
```

## JSONの閲覧方法

**XBRL-HOME/web/index.html** をウェブブラウザで開くと JSONの中身を確認できます。
※ ajaxでローカルファイルを読むので **Chrome** の場合はローカルサーバーが必要です。

