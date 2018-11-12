time_names_list = [
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

time_names_order = time_names_list.map(x => x[0]);

time_names = {};
for(var x of time_names_list){
    time_names[x[0]] = x[1];
}

summary_time_names = [
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
