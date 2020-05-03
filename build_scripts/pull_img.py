#!/usr/bin/python3
import boto3
import json
import docker
import os


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
    try:
        login_resp=client.login(paras['ecr_temp_auth']['username'], paras['ecr_temp_auth']['password'], registry=paras['ecr_temp_auth']['registry']) #login to repo
        print('Login succeded:', login_resp)
        try:
            auth_config={'username': paras['ecr_temp_auth']['username'], 'password': paras['ecr_temp_auth']['password']}
            pull_respone=client.images.pull(paras['image_tag'], auth_config=auth_config)
        except Exception as e:
            print('Error in oulling image:', e)
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
    pull_resp=pull_image_ecr(docker_client, fetched_paras)