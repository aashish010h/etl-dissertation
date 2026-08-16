#!/bin/bash

CLUSTER="your-cluster-name"
TASK_DEF="your-task-definition-name"
SUBNET="subnet-xxxxxxxx"
SG="sg-xxxxxxxx"

echo "Firing 50 Fargate tasks..."

for i in {1..5}; do
    aws ecs run-task \
        --cluster $CLUSTER \
        --task-definition $TASK_DEF \
        --launch-type FARGATE \
        --count 10 \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SG],assignPublicIp=ENABLED}" &
done

wait
echo "All Fargate tasks provisioned."