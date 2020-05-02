import boto3
import json
import docker
import os
from io import BytesIO
import base64


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
    print("Parameters fetched:", para_value_dict)
    return para_value_dict

    
if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetched_paras=fetch_parameter(para_name) #fetch para
    image_object=build_image(docker_client, fetched_paras, work_space_path) #build image
    ecr_push_image=push_image(docker_client, image_object) 