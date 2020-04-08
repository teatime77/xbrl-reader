# 処理フロー

```eval_rst
.. graphviz::

    digraph foo {
        graph [fontname = "MS Gothic"];
        node [fontname = "MS Gothic"];
        edge [fontname = "MS Gothic"];   

        EDINET [ shape=cylinder, label="金融庁のEDINET"];
        report_zip [ shape=box3d, label="インラインXBRL\nXBRLインスタンス\n提出者別タクソノミ\nマニフェスト"];
        
        xbrl_zip [ shape=box3d, label="XBRLインスタンス"];
        summary_012 [ shape=box, label="summary_0.csv, summary_1.csv, summary_2.csv" ];
        company [ shape=box, label="会社情報"];
        summary_join [ shape=box, label="summary_join.csv" ];
        pickle [ shape=box, label="preprocess-*.pickle" ];

        proc1 [ shape = box, label = "ZIPファイルをダウンロード ( download.py )", style = "rounded" ];
        proc2 [ shape = box, label = "XBRLインスタンスを抽出 ( extract.py )", style = "rounded" ];
        proc3 [ shape = box, label = "XBRL→CSV作成 ( summary.py )", style = "rounded" ];

        proc4 [ shape = box, label = "表を結合(make_summary_join.ipynb)", style = "rounded" ];
        proc5 [ shape = box, label = "財務分析のサンプルアプリ", style = "rounded" ];

        proc6 [ shape = box, label = "業績予想の前処理(preprocess.ipynb)", style = "rounded" ];
        proc7 [ shape = box, label = "業績予想 ( sklearn.ipynb, TensorFlow.ipynb )", style = "rounded" ];
        
        EDINET -> proc1 -> report_zip -> proc2 -> xbrl_zip -> proc3 -> summary_012;

        summary_012 -> proc4;
        company -> proc4;
        proc4 -> summary_join -> proc5;

        summary_012 -> proc6;
        company -> proc6;
        proc6 -> pickle -> proc7;
   }
```

