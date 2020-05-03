#!/usr/bin/python3
import json
import docker
import boto3


#fetch parameters from ssm
def fetch_parameter(para):
    #set ssm client
    print("Fetching paras from parameter store.")
    ssm_client=boto3.client('ssm', region_name='ap-south-1')

    response = ssm_client.get_parameter(
        Name=para
    )
    para_value=response['Parameter']['Value']
    para_value_dict=json.loads(para_value)
    print('Parameters fetched')
    return para_value_dict


#stop containers
def stop_containers(para_name):
    print("stopping")


if __name__ == "__main__":
    para_name='django-helloworld'
    docker_client=docker.from_env()
    #calls
    fetched_paras=fetch_parameter(para_name)
    stop_resp=stop_containers(fetched_paras)
    
