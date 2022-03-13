# Prefect PR 

The purpose of this tutorial is to walk through how to leverage ECS Capacity Providers in run_task_kwargs of ECSAgent and ECSRun. Below you will find the commands and Prefect Flows used. 

Requirements: 
* [Conda](https://docs.conda.io/en/latest/miniconda.html) and Python 3.7+
* Existing Prefect Server or Cloud Account
* AWS Access 
* AWS CLI Installed and Configured

## Example of Expected Outcome

Using Capacity Provider in ECSRun

![](./agent-capacity-prov-final.gif)

## Setting up Environment 

Create a virtual environment with Conda

```sh
conda create -n ecs_capacity_provider python=3.7 
conda activate ecs_capacity_provider 
conda install gh --channel conda-forge
```

Clone prefect, go into the cloned directory and checkout the ecs_capacity_provider PR

```sh 
git clone https://github.com/PrefectHQ/prefect.git
cd prefect 
gh pr checkout 5411
```

## Setting up Prefect and Prefect Cloud
While in the cloned prefect directory install the requirements

```sh
pip install -e ".[dev, aws]"
```

Sign into [Prefect Cloud](https://cloud.prefect.io/) and get an auth token

    - [Create API Key](https://cloud.prefect.io/user/keys)

Switch to Backend of Prefect Cloud and Login

```sh
prefect backend cloud
prefect auth login -k <your auth token>
```

Create a project to test on

```sh
prefect create project "ECS Test"
```

## Creating ECS Cluster and ECS Agent

Create the ECS Cluster

```sh
aws ecs create-cluster --cluster-name PrefectECS \
--capacity-providers FARGATE_SPOT FARGATE \
--default-capacity-provider-strategy \
capacityProvider=FARGATE_SPOT,weight=3 \
capacityProvider=FARGATE,base=1,weight=2 \
--region us-east-1
```

Create the S3 Bucket to store the Flow

```bash
aws s3api create-bucket \
    --bucket prefect \
    --region us-east-1
```


## Running the ECSAgent on a CapacityProvider

First create a file called agent_capacity_provider.yaml that has the capacityProviderStrategy and awsvpc defined

```yaml
cluster: prefectEcsCluster
capacityProviderStrategy:
  - capacityProvider: FARGATE_SPOT
    weight: 1
    base: 0
networkConfiguration:
  awsvpcConfiguration:
    subnets: [subnet-0d30148cb7ae73ef4, subnet-082033f253a971609]
    securityGroups: []
    assignPublicIp: ENABLED
```

Then create the Capacity Provider ECS Agent with the following command

```bash
prefect agent ecs start \
--name ECS-Local \
--cluster arn:aws:ecs:us-east-1:084679824415:cluster/PrefectECS \
--task-role-arn arn:aws:iam::084679824415:role/ecsTaskExecutionRole \
--log-level DEBUG \
--label ecs-agent-local \
--run-task-kwargs ../agent_capacity_provider.yaml
```

Next run the flow below, since nothing is passed into ECSRun the Agent's ECS Capacity Provider will be used to run the flow.

<details><summary>See Execution of Agent</summary>

**Note**: The red error in the snippit below shows that the virtual environment associated with this walkthrough is active 

![agent-capacity-prov](https://user-images.githubusercontent.com/34378029/158037265-a3f4b1f2-d3bc-40b3-be89-3a652b94faa1.gif)

 
</details>


<details><summary>See Flow</summary>


```python
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


run_config = ECSRun()

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
```

</details>



## Using Capacity Provider via ECSRun when using a Fargate ECS Agent

Start the ECS Agent with the default Fargate Launch Type

**Note**: Ensure The ECS Task Execution Policy has S3 Access

```sh
prefect agent ecs start \
--name ECS-Local \
--cluster arn:aws:ecs:us-east-1:084679824415:cluster/PrefectECS \
--task-role-arn arn:aws:iam::084679824415:role/ecsTaskExecutionRole \
--log-level DEBUG \
--label ecs-agent-local 
```

Run the Flow with a capacity provider and not the ECS Agent's launch

<details><summary>See Flow details</summary>

By passing capacityProviderStrategy into ECSRun's run_task_kwargs parameter we are able to run the flow with the capacity provider of the cluster

```python
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
```
</details>


