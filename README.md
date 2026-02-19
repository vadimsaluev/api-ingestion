How to use this repo:

1. Steps of the case study are in respective folders. Navigate them one by one to find case study solution steps.
2. Summaries on theory and necessary execution steps are documented in README.md files, refer to them when necessary.
3. This case study is not a production-ready solution, some exercises will still be required to put everything together.

Very important:
Below are summarised cost assumptions, please assess them from this file, as with this data volume as in this case study even after 3-5 years of data ingestion, infrastructure cost is negligible except for orchestration. The main architectural decision impacting TCO is whether to use Cloud Composer or a lightweight orchestration strategy. Even organic grouth with such small data is not a significant cost center, however, starting from 1TB of data, yearly costs for storage become a significant in comparison with other pipeline cost components (from €240/year and up to >€10000/year for tens of TBs).

All figures are approximate, to illustrate cost component balance (infra only, no salary funds):

----
Initial investments (one-off for initial setup) if managed orchestration is preferred:
----
Container Registry      - ~€350/first month

----
Managed orchestration strategy:
----
Cloud Run ingestion     - ~€5
GCS Bronze              - ~€0,05
BQ Storage              - ~€0,05
BQ Queries              - ~€2 (not including analytics)
Cloud Composer          - ~$4500 <- main cost driver in case of mnanaged orchestration strategy

----
Lean approach (no Composer)
----
Cloud Run ingestion     - ~€5
GCS Bronze              - ~€0,05
BQ Storage              - ~€0,05
BQ Queries              - ~€2 (not including analytics)
Airflow+dbt VM          - ~$500 <- less than Cloud Composer, but somebody will need to oversee the VM