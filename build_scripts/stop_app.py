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
    root_para=json.loads(para_value)
    if root_para['deployment_type'] == 'lift_shift': 
        deployment_para_name='/'+root_para['image_name']+'/'+root_para['deployment_type']
        deployment_para_resp=ssm_client.get_parameter(
            Name=deployment_para_name
        )
        return root_para, json.loads(deployment_para_resp['Parameter']['Value'])['lift_shift']
    elif root_para['deployment_type'] == 'cloud_optimised': 
        print('redundant')
        return 'para not found'


#stop container
def stop_container(client, root_para, deployment_para):
    root_para_image_name=root_para['image_name']
    current_context={}
    [current_context.update(context) for context in deployment_para if context['image_name']==root_para_image_name]
    try:
        client.stop(current_context['container_name'])
    except Exception as e:
        print('Exception in loggin in:', e)


#delete container
def delete_container(client, paras):
    root_para_image_name=root_para['image_name']
    current_context={}
    [current_context.update(context) for context in deployment_para if context['image_name']==root_para_image_name]
    try:
        client.remove_container(current_context['container_name'])
    except Exception as e:
        print('Exception in loggin in:', e)


#delete image
def delete_image(client, root_para, deployment_para):
    image_name_template=root_para['image_repo_name'].replace("<aws_account_id>", root_para['aws_account_id']).replace("<aws_region>", root_para['aws_region'])+'/'+root_para['image_name']
    image_name=image_name_template+':'+root_para['image_tag']
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
    root_para, deployment_para=fetch_parameter(para_name) #fetch para
    stop_container(client, root_para, deployment_para) #stop running instance of app
    delete_container(client, deployment_para)
    delete_image(client, root_para, deployment_para) #delete current app image