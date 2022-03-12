from prefect import task, Flow

from prefect import task, Flow
from prefect.run_configs import ECSRun
import random
from prefect.storage import S3


@task
def random_number():
    return random.randint(0, 100)


@task
def plus_one(x):
    return x + 1


run_config = ECSRun(
    run_task_kwargs=dict(capacityProviderStrategy=[{'capacityProvider': 'FARGATE_SPOT', 'weight': 0, 'base': 1}])
)

storage = S3(
    bucket="aidata-ig",
    key="prefect/flows/test_capacity_provider.py",
    client_options={"use_ssl": False},
    stored_as_script=True,
    # this will ensure to upload the Flow script to S3 during registration
    local_script_path='test_capacity_provider.py'
    )


with Flow("My Functional Flow", run_config=run_config, storage=storage) as flow:
    r = random_number()
    y = plus_one(x=r)

flow.register(
    project_name="ECS Test", labels=["ecs-agent-local"], add_default_labels=False
)
