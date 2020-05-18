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


#pull image from ecr
def run_container(client, root_para, deployment_para):
    ecr_client=boto3.client('ecr', region_name='ap-south-1')
    try:
        root_para_image_name=root_para['image_name']
        current_context={}
        [current_context.update(context) for context in deployment_para if context['image_name']==root_para_image_name]
        image_name_template=root_para['image_repo_name'].replace("<aws_account_id>", root_para['aws_account_id']).replace("<aws_region>", root_para['aws_region'])+'/'+root_para['image_name']
        auth_resp=ecr_client.get_authorization_token() #get ecr temp auth tokern
        user, passwd=base64.b64decode(auth_resp['authorizationData'][0]['authorizationToken']).decode().split(':')
        registry=auth_resp['authorizationData'][0]['proxyEndpoint']
        login_resp=client.login(user, passwd, registry=registry) #login to repo
        print('Login succeded:', login_resp)
        auth_config={'username': user, 'password': passwd} #build creds for pushing image to ecr
        image_name=image_name_template+':'+root_para['image_tag']
        print('Image used to run container:', image_name)
        client.containers.run(image_name, detach=True, ports={'8000/tcp': 8000}, name=current_context['container_name']) #run container
        print('{} container started'.format(current_context['container_name']))
    except Exception as e:
        print('Exception in loggin in:', e)

    
if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    root_para, deployment_para=fetch_parameter(para_name) #fetch para
    run_container(docker_client, root_para, deployment_para)