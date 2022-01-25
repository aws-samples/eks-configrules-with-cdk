#!/bin/bash
# Enable logging with the following command
REGION=''
CLUSTER=''

aws eks update-cluster-config \
    --region $REGION \
    --name $CLUSTER \
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'