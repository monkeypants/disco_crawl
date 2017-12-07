Introduction
============

The purpose of this software is to create an up-to date index of all web content in the .GOV.AU domain.

This is a re-engineered and updated version of the legacy disco_crawl project from 2015. That code is archived in the 2015_legacy branch of this repo.

Apart from a bit of library rot, the significant problem with the old crawler is that it became inefficient as multiple crawler nodes were run in parallel.

This new version:

 * Breaks the code into 3 types of nodes which are all horisontally scalable (nodes can be added/removed to support crawling workload) without any loss of efficiency. The previous version had 2 layers (crawler and index manager)
 * Employs external message queues between all nodes ("competitive consumer" pattern). The pervious version had "competitive consumers" updating the index, but used internal queues within the crawler node that prevented coreography.
 * Uses a "shared cache" to improve traffic efficiency.

.. graphviz::

   digraph d {
      node [shape=component style=filled fillcolor=lightblue];

      www [label="gov.au\ncontent" fillcolor=white];
      q1 [label="<<AWS SQS>>\nmessage queue\ncrawl this!" fillcolor=lightyellow];
      cli [label="command\nline\ninterface" shape=ellipse fillcolor=white];
      manager [label="<<GovCloud>>\nprocess manager"];
      cli -> manager -> q1;
      subgraph cluster_crawlers {
         label="as many as needed";
	 crawler [label="<<GovCloud>>\ncrawler node"];
      }
      crawler -> q1;
      www -> crawler [dir=back];
      q2 [label="<<AWS SQS>>\nmessage queue\n(was crawled)\nindex this!" fillcolor=lightyellow];
      crawler -> q2;
      s3data [label="<<AWS S3>>\nfetched content" fillcolor=lightyellow];
      crawler -> s3data;
      cache [label="<<AWS ElasticCache>>\nshared cache\nshared config\n(don't fetch again)\n(don't be too brutal)" fillcolor=lightyellow];
      crawler -> cache;
      manager -> cache;
      subgraph cluster_indexer {
         label="as many as needed";
         indexer [label="<<GovCloud>>\nindexer node"];
      }
      q2 -> indexer [dir=back];
      q1 -> indexer [dir=back];
      s3data -> indexer [dir=back];
      cache -> indexer [dir=back];
      index [label="<<hosted elastic search>>\nindex" fillcolor=green];
      indexer -> index;
      iq [label="useful\nquestions" shape=ellipse fillcolor=white];
      index -> iq [dir=back];
   }
