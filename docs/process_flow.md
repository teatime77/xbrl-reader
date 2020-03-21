# 処理フロー

```eval_rst
.. graphviz::

    digraph foo {
        graph [fontname = "MS Gothic"];
        node [fontname = "MS Gothic"];
        edge [fontname = "MS Gothic"];   

        EDINET [ shape=cylinder, label="EDINET"];
        report_zip [ shape=box3d, label="インラインXBRL\nXBRLインスタンス\n提出者別タクソノミ\nマニフェスト"];
        
        xbrl_zip [ shape=box3d, label="XBRLインスタンス"];
        summary_012 [ shape=box, label="summary_0.csv, summary_1.csv, summary_2.csv" ];
        company [ shape=box, label="会社情報"];
        summary_join [ shape=box, label="summary_join.csv" ];

        proc1 [ shape = box, label = "ZIPファイルをダウンロード", style = "rounded" ];
        proc2 [ shape = box, label = "XBRLインスタンスを抽出", style = "rounded" ];
        proc3 [ shape = box, label = "XBRL→CSV作成", style = "rounded" ];
        proc4 [ shape = box, label = "表を結合", style = "rounded" ];

        EDINET -> proc1 -> report_zip -> proc2 -> xbrl_zip -> proc3 -> summary_012;
        summary_012 -> proc4;
        company -> proc4;
        proc4 -> summary_join;
   }
```

　  
　  
1. 金融庁の[EDINET](https://disclosure.edinet-fsa.go.jp/)からZIPファイルをダウンロードします。
2. ZIPファイルの中からXBRLインスタンスファイルを抽出します。
3. XBRLインスタンスファイルから **summary-0.csv**, **summary-1.csv**, **summary-2.csv** を作ります。
4. **summary-0.csv**, **summary-1.csv**, **summary-2.csv** と会社情報から **summary-join.csv** を作ります。
