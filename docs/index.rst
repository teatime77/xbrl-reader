.. mynote documentation master file, created by
   sphinx-quickstart on Fri Mar 20 17:45:04 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

XBRL Reader
==================================

| 金融庁の `EDINET <https://disclosure.edinet-fsa.go.jp/>`_ から上場企業の決算情報(XBRLファイル)をダウンロードし、
| XBRLファイルからCSVファイルを作成します。

.. toctree::
   :maxdepth: 0
   :caption: 目次:

   context.md
   csv.md
   process_flow.md
   exec.md

   module/index

| Qiitaの記事もご覧ください。
| `全上場企業の過去５年間の決算情報をCSVファイルに変換 <https://qiita.com/teatime77/items/e5aa2d9027749768f50d>`_

| ソースはGitHubにあります。
| https://github.com/teatime77/xbrl-reader

.. plantuml
   .. uml::

      Alice -> Bob: Hi!
      Alice <- Bob: How are you?


* :ref:`genindex`
* :ref:`modindex`

.. * :ref:`search`