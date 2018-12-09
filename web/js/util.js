period_names_list = [
    ["FilingDateInstant"    , "提出日時点"],
    ["CurrentYearInstant"   ,"当期連結時点"],
    ["CurrentYearDuration"  , "当期連結期間"],
    ["CurrentQuarterInstant", "当四半期会計期間連結時点"],
    ["CurrentQuarterDuration", "当四半期会計期間連結期間"],
    ["CurrentYTDDuration"   , "当四半期累計期間連結期間"],
    ["Prior1YTDDuration"    , "前年度同四半期累計期間連結期間"],
    ["Prior1QuarterInstant" , "前年度同四半期会計期間連結時点"],
    ["Prior1QuarterDuration", "前年度同四半期会計期間連結期間"],
    ["Prior1YearInstant"    , "前期連結時点"],
    ["Prior1YearDuration"   , "前期連結期間"],
    ["Prior2YearInstant"    , "前々期連結時点"],
    ["Prior2YearDuration"   ,"前々期連結期間"],
    ["Prior3YearInstant"    ,"3期前連結時点"],
    ["Prior3YearDuration"   ,"3期前連結期間"],
    ["Prior4YearInstant"    ,"4期前連結時点"],
    ["Prior4YearDuration"   ,"4期前連結期間"],
    ["Prior2InterimInstant" , "Prior2InterimInstant"],
    ["InterimInstant"       , "InterimInstant"],
    ["InterimDuration"      , "InterimDuration"],
    ["Prior1InterimInstant" , "Prior1InterimInstant"],
    ["Prior1InterimDuration", "Prior1InterimDuration"],
    ["Prior2InterimDuration", "Prior2InterimDuration"],
    ["Prior5YearInstant"    , "Prior5YearInstant"],
    ["Prior5YearDuration"   , "Prior5YearDuration"],
];

period_names_order = period_names_list.map(x => x[0]);

period_names = {};
for(var x of period_names_list){
    period_names[x[0]] = x[1];
}

summary_period_names = [
    "FilingDateInstant"    ,
    "CurrentYearInstant"   ,
    "CurrentYearDuration"  ,
    "CurrentQuarterInstant",
    "CurrentQuarterDuration",
    "CurrentYTDDuration"   ,
];

summary_text_items = [
    "DocumentTitleCoverPage",
    "QuarterlyAccountingPeriodCoverPage",
    "SemiAnnualAccountingPeriodCoverPage",
    "FiscalYearCoverPage",
    "CompanyNameCoverPage",
    "TitleAndNameOfRepresentativeCoverPage",
    "AddressOfRegisteredHeadquarterCoverPage",
    "EDINETCodeDEI",
    "SecurityCodeDEI",
    "DocumentTypeDEI",
    "AccountingStandardsDEI",
    "TypeOfCurrentPeriodDEI",
    "IdentificationOfDocumentSubjectToAmendmentDEI",
];


type_dic = {
    "stringItemType": "文字列",
    "booleanItemType": "ブール値",
    "dateItemType": "日付",
    "nonNegativeIntegerItemType": "非負整数",
    "textBlockItemType": "テキストブロック",
    "monetaryItemType": "金額",
    "perShareItemType": "一株当たり金額",
    "percentItemType": "割合(%)",
    "decimalItemType": "小数",
    "sharesItemType": "株数",
    "domainItemType": "ドメイン",
    "pureItemType": "純粋型"
}

category_names = {
    'metal' : '金属製品',
    'mining' : '鉱業',
    'steel' : '鉄鋼',
    'rubber' : 'ゴム製品',
    'nonferrous_metal' : '非鉄金属',
    'insurance' : '保険業',
    'electronics' : '電気機器',
    'warehouse_transport' : '倉庫・運輸関連',
    'glass_soil_stone' : 'ガラス・土石製品',
    'textile' : '繊維製品',
    'finance' : 'その他金融業',
    'petroleum_coal' : '石油・石炭製品',
    'electric_power_gas' : '電気・ガス業',
    'pulp_paper' : 'パルプ・紙',
    'retail' : '小売業',
    'transport_equipment' : '輸送用機器',
    'machinery' : '機械',
    'brokerage' : '証券、商品先物取引業',
    'pharmaceutical' : '医薬品',
    'chemistry' : '化学',
    'precision_instrument' : '精密機器',
    'land_transport' : '陸運業',
    'marine_transport' : '海運業',
    'air_transport' : '空運業',
    'real_estate' : '不動産業',
    'food' : '食料品',
    'bank' : '銀行業',
    'wholesale' : '卸売業',
    'other_product' : 'その他製品',
    'fishing_agriculture' : '水産・農林業',
    'service' : 'サービス業',
    'construction' : '建設業',
    'information_communication' : '情報・通信業',
    'foreign_government' : '外国政府等',
    'foreign_corporation' : '外国法人・組合',
    'other_foreign_corporation' : '外国法人・組合（有価証券報告書等の提出義務者以外）',
    'domestic_corporation' : '内国法人・組合（有価証券報告書等の提出義務者以外）',
    'private_person' : '個人（組合発行者を除く）',
    'private_person_non_resident' : '個人（非居住者）（組合発行者を除く）',
};
