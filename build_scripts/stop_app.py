#!/usr/bin/python3
import boto3
import json
import docker
import os
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
    print('Parameters fetched')
    return para_value_dict


#stop container
def stop_container(client, paras):
    try:
        client.stop(paras['container_name'])
    except Exception as e:
        print('Exception in loggin in:', e)


#delete container
def delete_container(client, paras):
    try:
        client.remove_container(paras['container_name'])
    except Exception as e:
        print('Exception in loggin in:', e)


#delete image
def delete_image(client, paras):
    image_name=paras['ecr_repo_uri']+':'+paras['image_tag']
    try:
        client.remove_image(image_name, force=True)
    except Exception as e:
        print('Exception in loggin in:', e)

    
if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    client=docker.APIClient(base_url='unix://var/run/docker.sock') #low level api client
    #calls 
    fetched_paras=fetch_parameter(para_name) #fetch para
    stop_container(client, fetched_paras)
    delete_image(client, fetched_paras)