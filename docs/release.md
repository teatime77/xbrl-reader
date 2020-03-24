# リリース履歴

### 2020年3月23日

#### プログラムの変更

* 会計基準の [IFRS](https://ja.wikipedia.org/wiki/%E5%9B%BD%E9%9A%9B%E8%B2%A1%E5%8B%99%E5%A0%B1%E5%91%8A%E5%9F%BA%E6%BA%96) に一部対応しました。  
IFRSの項目のうち冗長ラベルが **Japan GAAP** の項目と対応するものはCVSファイルに出力するようにしました。  
例えば冗長ラベルが"資本（IFRS）"の項目は、 **Japan GAAP** の"資本"と同じとみなします。
  
* [勘定科目の出現回数](freq_stats.md) を会計基準ごとに集計するようにしました。
  
* **処理３** の **summary.py** を実行すると **python/data/calc_tree.txt** に、XBRLの計算リンクによるツリーを出力するようにしました。  
ツリーは項目間の計算の依存関係を示すものですが、まだ開発中の機能です。

#### データの更新

EDINETから最新のデータをダウンロードしました。
新しいプログラムで作成したデータを以下にアップロードしました。

##### **処理２** のextract.pyの出力ファイル

* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-0.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-0.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-1.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-1.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-2.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-2.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-3.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-3.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-4.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-4.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-5.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-5.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-6.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-6.tar)  
* [http://lkzf.info/xbrl/data/2020-03-24/extract/extract-7.tar](http://lkzf.info/xbrl/data/2020-03-24/extract/extract-7.tar)  

##### **処理３** の出力ファイル

* [http://lkzf.info/xbrl/data/2020-03-24/summary-0.csv](http://lkzf.info/xbrl/data/2020-03-24/summary-0.csv)  
* [http://lkzf.info/xbrl/data/2020-03-24/summary-1.csv](http://lkzf.info/xbrl/data/2020-03-24/summary-1.csv)  
* [http://lkzf.info/xbrl/data/2020-03-24/summary-2.csv](http://lkzf.info/xbrl/data/2020-03-24/summary-2.csv)  
* [http://lkzf.info/xbrl/data/2020-03-24/stats.txt](http://lkzf.info/xbrl/data/2020-03-24/stats.txt)  
* [http://lkzf.info/xbrl/data/2020-03-24/calc_tree.txt](http://lkzf.info/xbrl/data/2020-03-24/calc_tree.txt)  

##### **処理４** の出力ファイル

* [http://lkzf.info/xbrl/data/2020-03-24/summary-join.csv](http://lkzf.info/xbrl/data/2020-03-24/summary-join.csv)  
