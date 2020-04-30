import boto3
import json
import docker


#fetch parameters from ssm
def fetch_parameter():
    ssm_client=boto3.client('ssm')
    response = ssm_client.get_parameter(
        Name='django-helloworld'
    )
    print(response)


if __name__ == "__main__":
    docker_client=docker.from_env() 
    ssm_fetch_para_response=fetch_parameter()