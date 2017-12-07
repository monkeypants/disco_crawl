# Crawler Node

Receives messages from SQS with domain names, and crawls pages to S3 and sends results to another SQS queue.

## Deployment

* create EC2 box with ubuntu
* add box to ~/.ssh/config
* run `provision.sh box-name`
* run `deploy.sh box-name`
* ssh to the box
* `cd /opt/crawler-node`
* run `docker-compose up --scale crawler=10 -d` and see how they do work in background.

t2.small instances: 10 workers, more are problematic (LA, memory)
t2.medium: 10 workers use all CPU so pointless to get more.

TODO: migrate to Govcloud deployment.