import boto3
import json
import docker


#fetch parameters from ssm
def fetch_parameter(para):
    #set ssm client
    ssm_client=boto3.client('ssm', region_name='ap-south-1')

    response = ssm_client.get_parameter(
        Name=para
    )
    print(response)


if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    ssm_fetch_para_response=fetch_parameter(para_name)