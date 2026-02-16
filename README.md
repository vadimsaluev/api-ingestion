# api-ingestion
A little playing around some data pipelines

ADR-0: Use a mock API, not the GA4 native integration with BigQuery.
    Rationale: Usually in production, in cases like this we should use the Occam's razor principle and do not increase IT complexity without strong neccessity. This means, that if same data as the data from this mock API is available for integration directly from GA4 feed, it is architecturally advised to use native integration between GA4 and GCP and ingest events directly without creating an additional potential breaking point.
    Implication: Since this exersise is done solely for tech. skills assessment, we assume that in this situation we have chosen from two comparable solutions options the scenario with leveraging an API as data source due to some random reasons wich we will not further consider. Just for the sake of keeping a historical Architectuire Decision Record - choosing another (recommended) option with native integration would affect the cost, the data model and overall downstream pipeline design, which we do not consider in the course of this evaluation.
