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


#pull image from ecr
def pull_image_ecr(client, paras):
    ecr_client=boto3.client('ecr', region_name='ap-south-1')
    try:
        auth_resp=ecr_client.get_authorization_token()
        user, passwd=base64.b64decode(auth_resp['authorizationData'][0]['authorizationToken']).decode().split(':')
        registry=auth_resp['authorizationData'][0]['proxyEndpoint']
        login_resp=client.login(user, passwd, registry=registry) #login to repo
        print('Login succeded:', login_resp)
        auth_config={'username': user, 'password': passwd} #build creds for pushing image to ecr
        image_name=paras['ecr_repo_uri']+':'+paras['image_tag']
        print('Image to be pulled:', image_name)
        client.images.pull(image_name, auth_config=auth_config) #push image
        print('Image pulled from ecr')
    except Exception as e:
        print('Exception in loggin in:', e)

    
if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetched_paras=fetch_parameter(para_name) #fetch para
    pull_image_ecr(docker_client, fetched_paras)