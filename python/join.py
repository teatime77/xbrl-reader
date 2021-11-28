import urllib.request
import pandas as pd

# 会社情報をダウンロードします。
urllib.request.urlretrieve("http://lkzf.info/xbrl/data/EdinetcodeDlInfo.csv", "data/EdinetcodeDlInfo.csv")

# 会社情報のCSVを読み込みます。
df会社 = pd.read_csv("data/EdinetcodeDlInfo.csv", encoding='cp932', skiprows=[0])
df会社 = df会社.set_index('ＥＤＩＮＥＴコード')

# summary-0.csv, summary-1.csv, summary-2.csv を Pandasに読み込みます。
df提出日時点 = pd.read_csv("data/summary-0.csv", parse_dates=[ '提出日', '当事業年度開始日', '当事業年度終了日', '会計期間終了日' ])
df時点 = pd.read_csv("data/summary-1.csv")
df期間 = pd.read_csv("data/summary-2.csv")

# 長い項目名を短くします。
df時点 = df時点.rename(columns={ 
    '１株当たり純資産額': '１株当たり純資産',
    '平均年齢（年）'    : '平均年齢',
    '平均勤続年数（年）': '平均勤続年数',
})

df期間 = df期間.rename(columns={ 
    '売上総利益又は売上総損失（△）'            :'売上総利益', 
    '経常利益又は経常損失（△）'                : '経常利益', 
    '営業利益又は営業損失（△）'                : '営業利益',
    '当期純利益又は当期純損失（△）'            :'純利益', 
    '税引前当期純利益又は税引前当期純損失（△）':'税引前純利益', 
    '１株当たり当期純利益又は当期純損失（△）'  :'１株当たり純利益',
    '親会社株主に帰属する当期純利益又は親会社株主に帰属する当期純損失（△）': '親会社株主に帰属する純利益',
    '潜在株式調整後1株当たり当期純利益'         :'調整1株当たり純利益',
    '現金及び現金同等物の増減額（△は減少）'    :'現金及び現金同等物の増減' 
})


# 平均年間給与が１万円未満とか１億円以上とかありえないでしょ。
print(df時点[(df時点['平均年間給与'] < 10000) | (10000*10000 < df時点['平均年間給与'])]['平均年間給与'])
df時点.loc[(df時点['平均年間給与'] < 10000) | (10000*10000 < df時点['平均年間給与']), '平均年間給与'] = pd.np.nan


# 有価証券報告書だけ抜き出します。
df提出日時点 = df提出日時点[ df提出日時点['報告書略号'] == "asr" ]
df時点       = df時点[ df時点['報告書略号'] == "asr" ]
df期間       = df期間[ df期間['報告書略号'] == "asr" ]


# コンテキストごとにデータを抜き出します。
df提出日時点 = df提出日時点.reset_index()

df当期連結時点 = df時点[df時点['コンテキスト'] == '当期連結時点'].reset_index()
df当期個別時点 = df時点[df時点['コンテキスト'] == '当期個別時点'].reset_index()

df当期連結期間 = df期間[df期間['コンテキスト'] == '当期連結期間'].reset_index()
df当期個別期間 = df期間[df期間['コンテキスト'] == '当期個別期間'].reset_index()

df前期連結時点 = df時点[df時点['コンテキスト'] == '前期連結時点'].reset_index()
df前期個別時点 = df時点[df時点['コンテキスト'] == '前期個別時点'].reset_index()

df前期連結期間 = df期間[df期間['コンテキスト'] == '前期連結期間'].reset_index()
df前期個別期間 = df期間[df期間['コンテキスト'] == '前期個別期間'].reset_index()

assert len(df提出日時点) == len(df当期連結時点) == len(df当期個別時点) == len(df当期連結期間) == len(df当期個別期間) == len(df前期連結時点) == len(df前期個別時点) == len(df前期連結期間) == len(df前期個別期間)


# 前期の項目名に "前期" を付加します。
df前期連結時点 = df前期連結時点.rename(columns={ '資産':'前期資産' })
df前期連結期間 = df前期連結期間.rename(columns={ '売上高':'前期売上高', '純利益':'前期純利益' })
df前期個別時点 = df前期個別時点.rename(columns={ '資産':'前期資産' })
df前期個別期間 = df前期個別期間.rename(columns={ '売上高':'前期売上高', '純利益':'前期純利益' })


# コンテキストごとに分かれているデータを一つにまとめます。
drop_columns = ['EDINETコード', '会計期間終了日', '報告書略号', 'コンテキスト', '平均年齢', '平均勤続年数', '平均年間給与', '発行済株式総数', '１株当たり配当額', 'index' ]

for 連結_個別 in [ "連結", "個別" ]:

    if 連結_個別 == "連結":
        df = pd.concat([ 
            df提出日時点[['EDINETコード', '証券コード', '提出日', '会計期間終了日']], 
            df当期連結時点[ [x for x in df当期連結時点.columns if x not in drop_columns ] ], 
            df当期連結期間[ [x for x in df当期連結期間.columns if x not in drop_columns ] ],
            df前期連結時点[['前期資産']],
            df前期連結期間[['前期売上高', '前期純利益']],
            df当期個別時点[[ '平均年齢', '平均勤続年数', '平均年間給与', '発行済株式総数']], 
            df当期個別期間[['１株当たり配当額']]
        ], 
        axis=1)

    else:
        df = pd.concat([ 
            df提出日時点[['EDINETコード', '証券コード', '提出日', '会計期間終了日']], 
            df当期個別時点[ [x for x in df当期個別時点.columns if x not in drop_columns ] ], 
            df当期個別期間[ [x for x in df当期個別期間.columns if x not in drop_columns ] ],
            df前期個別時点[['前期資産']],
            df前期個別期間[['前期売上高', '前期純利益']],
            df当期個別時点[[ '平均年齢', '平均勤続年数', '平均年間給与', '発行済株式総数']], 
            df当期個別期間[['１株当たり配当額']]
        ], 
        axis=1)

    assert len(df) == len(df提出日時点)


    # 財務指標を計算します。
    df['粗利益'] = df['売上高'] - df['売上原価']

    df['売上高総利益率']   = df['粗利益']   / df['売上高']
    df['売上高営業利益率'] = df['営業利益'] / df['売上高']
    df['売上高経常利益率'] = df['経常利益'] / df['売上高']

    df['売上高販管費率'] = df['販売費及び一般管理費'] / df['売上高']

    df['総資本回転率']     = df['売上高'] / df['資産']
    df['流動比率']         = df['流動資産'] / df['流動負債']

    df['売上高変化率'] = (df['売上高'] - df['前期売上高']) / df['前期売上高']
    df['純利益変化率'] = (df['純利益'] - df['前期純利益']) / df['前期純利益']

    df['期首期末平均資産'] = (df['前期資産'] + df['資産']) / 2.0

    df['総資産経常利益率'] = df['経常利益'] / df['期首期末平均資産']

    df['総資産純利益率']   = df['純利益']   / df['期首期末平均資産']

    df['総資産親会社株主に帰属する純利益率']   = df['親会社株主に帰属する純利益'] / df['期首期末平均資産']

    df['自己資本'] = df['株主資本'].fillna(0) + df['評価・換算差額等'].fillna(0)

    df['有利子負債'] = df['短期借入金'].fillna(0) + df['1年内返済予定の長期借入金'].fillna(0) + df['1年内償還予定の社債'].fillna(0) + df['長期借入金'].fillna(0)      + df['社債'].fillna(0) + df['転換社債型新株予約権付社債'].fillna(0) + df['コマーシャル・ペーパー'].fillna(0)



    # 会社名から "株式会社" を取り除きます。
    df会社['提出者名'] = df会社['提出者名'].apply(lambda x: x.replace('株式会社', '').strip())


    # 会社名と業種をセットします。
    df['会社名']  = df['EDINETコード'].map(lambda x: df会社.loc[x]['提出者名'])
    df['業種']  = df['EDINETコード'].map(lambda x: df会社.loc[x]['提出者業種'])


    # 結果をCSVファイルに書きます。
    if 連結_個別 == "連結":
        df.to_csv('data/summary-join.csv', index=False)
    else:
        df.to_csv('data/summary-join-kobetsu.csv', index=False)
