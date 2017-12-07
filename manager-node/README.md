# Management Node

* sends new crawl jobs to requests queue
* receives results from response queue
  * puts them to Elastic
  * and to RDS backend (postgres, aurora, so on)
* keeps the list of crawled domains (recently sent to the crawlers) to avoid duplicate crawls
