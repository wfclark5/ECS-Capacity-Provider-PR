prefect agent ecs start \
--name ECS-Local \
--cluster arn:aws:ecs:us-east-1:084679824415:cluster/PrefectECS \
--task-role-arn arn:aws:iam::084679824415:role/ecsTaskExecutionRole \
--log-level DEBUG \
--label ecs-agent-local \
--run-task-kwargs ../agent_capacity_provider.yaml