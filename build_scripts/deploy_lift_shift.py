import boto3
import json
import docker
import os
import time


#fetch parameters from ssm
def fetch_parameter(para):
    #set ssm client
    print("Fetching paras from parameter store.")
    ssm_client=boto3.client('ssm', region_name='ap-south-1')
    response=ssm_client.get_parameter(
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


#deployment controller
def lift_shift_deployment_controller(root_para, deployment_para):
    image_name=root_para['image_name']
    current_context={}
    [current_context.update(context) for context in deployment_para if context['image_name']==image_name] #create current context para
    application_name=create_deployment_app(root_para, current_context) #get application name
    list_deployment_groups(root_para, current_context)

    return current_context


#create deployment app if not available
def create_deployment_app(root_para, context):
    client=boto3.client('codedeploy', region_name=root_para['aws_region'])
    try:    #check if deployment app exists
        response=client.get_application(
            applicationName=context['deployment_app_lift_shift']
        )
        print('Application {} already exists'.format(response['application']['applicationName']))
        return response['application']['applicationName'] #application name
    except Exception as e:
        if e.response['Error']['Code']=='ApplicationDoesNotExistException':  #application does not exist, create app, return name
            print('Application doesnt exist, creating')
            create_app_response=client.create_application(  
                applicationName=context['deployment_app_lift_shift'],
                computePlatform='Server'
            )
            print("Application {} created".format(context['deployment_app_lift_shift']))
            return context['deployment_app_lift_shift'] #application name
        else:
            print('Unexpected error encountered:', e)


#list deployment groups
def list_deployment_groups(root_para, context):
    client=boto3.client('codedeploy', region_name=root_para['aws_region'])
    dgs=[] #list of deployment groups
    try:
        list_dg_resp=client.list_deployment_groups(
            applicationName=context['deployment_app_lift_shift']
        )
        dgs.extend(list_dg_resp['deploymentGroups']) 
        if 'nextToken' in list_dg_resp:
            while list_dg_resp['nextToken'] in list_dg_resp: #list all dgs
                list_dg_resp=client.list_deployment_groups(
                    applicationName=app_name,
                    nextToken=list_dg_resp['nextToken']
                    )
                dgs.extend(list_dg_resp['deploymentGroups'])
        #iterate through all dgs and check if our dg exists if not create it
        if context['dg_lift_shift'] not in dgs:
            dg_id=create_deployment_group(root_para, context)  #create deployment group, return id
            print('dg didnt exist, created dg, dg id:', dg_id)
            return dg_id
        elif context['dg_lift_shift'] in dgs:
            dg_id=get_deployment_group(root_para, context)  #deployment group exists, fetch id
            print('dg exists, dg id:', dg_id)
            return dg_id
    except Exception as e:
        print('Unexpected error occured:', e)


#create deployment group
def create_deployment_group(root_para, context):
    client=boto3.client('codedeploy', region_name=root_para['aws_region'])
    try:
        response=client.create_deployment_group(
            applicationName=root_para['deployment_app_lift_shift'],
            deploymentGroupName=root_para['dg_lift_shift'],
            autoScalingGroups=[root_para['asg_lift_shift']],
            serviceRoleArn=root_para['code_deploy_service_role'],
            deploymentStyle={'deploymentType': 'IN_PLACE', 'deploymentOption': 'WITHOUT_TRAFFIC_CONTROL'}
        )
        return response['deploymentGroupId']
    except Exception as e:
        print('Unexpected error occured while creating deployment group:', e)


#get deploment group
def get_deployment_group(root_para, context):
    client=boto3.client('codedeploy', region_name=root_para['aws_region'])
    response=client.get_deployment_group(
        applicationName=context['deployment_app_lift_shift'],
        deploymentGroupName=context['dg_lift_shift']
    )
    return response['deploymentGroupInfo']['deploymentGroupId']


#create deployment
def create_deployment(root_para, context):
    client=boto3.client('codedeploy', region_name=root_para['aws_region'])
    response=client.create_deployment(
        applicationName=context['deployment_app_lift_shift'],
        deploymentGroupName=context['dg_lift_shift'],
        revision={
            'revisionType': 'S3',
            's3Location': {
                'bucket': root_para['artifact_bucket_name'],
                'key': root_para['s3_key'],
                'bundleType': 'zip'
            }
        }
    )
    deployment_status=describe_deployment(response['deploymentId'], client) #describe deployment
    print('Current deployment status is {}'.format(deployment_status))
    

#describe deployments
def describe_deployment(id, client):
    try:
        response=client.get_deployment(
            deploymentId=id
        )
        return response['deploymentInfo']['status']
    except Exception as e:
        print('Unexpected error while getting deployment status:', e)


if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    root_para, deployment_para=fetch_parameter(para_name) #fetch para
    current_context=lift_shift_deployment_controller(root_para, deployment_para)
    deployment_id=create_deployment(root_para, current_context)