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
    root_para_response=ssm_client.get_parameter(
        Name=para
    )
    para_value=root_para_response['Parameter']['Value']
    root_para=json.loads(para_value)
    print('Deployment type:', root_para['deployment_type'])

    if root_para['deployment_type'] == 'cloud_native':
        #deployment specific para
        deployment_para_name = '/'+root_para['image_name']+'/'+root_para['deployment_type']
        get_deployment_para=ssm_client.get_parameter(
            Name=deployment_para_name
        )
        deployment_para=json.loads(get_deployment_para['Parameter']['Value'])

        return cloud_native_controller(root_para, deployment_para['cloud_native'])
    
    elif root_para['deployment_type'] == 'lift_shift':
        print('lift and shift deployment')


#describe service
def describe_service(root_para, context_para):
    ecs_client = boto3.client('ecs', region_name=root_para['aws_region'])
    try:
        response=ecs_client.describe_services(
            cluster=context_para['cluster_name'],
            services=[context_para['ecs_service_name']]
        )
        return response
    
    except Exception as e:
        print('Exception in describing service:', e)


#create new task definition
def register_task_definition(root_para, context):
    ecs_client = boto3.client('ecs', region_name=root_para['aws_region']) #client

    image_uri=root_para['ecr_repo_uri']+':'+root_para['image_tag']
    try:
        response=ecs_client.register_task_definition(
                family='django-jenkins-repo-def-cf',
                networkMode='bridge',
                containerDefinitions=[
                    {
                        'name': context['container_name'],
                        'image': image_uri,
                        'memory': 128,
                        'portMappings': [
                            {
                                'containerPort': 8000,
                                'hostPort': 0,
                                'protocol': 'tcp'
                            },
                        ],
                        'essential': True
                    },
                ],            
                requiresCompatibilities=[
                    'EC2',
                ]
            )
        return response
    except Exception as e:
        print('Exception in creating task def:', e)


#create service
def create_service(root_para, context, task_def):
    ecs_client = boto3.client('ecs', region_name=root_para['aws_region'])
    #try:
    print(context)
    response = ecs_client.create_service(
        cluster=context['cluster_name'],
        serviceName=context['ecs_service_name'],
        taskDefinition=task_def['taskDefinitionArn'],
        loadBalancers=[
            {
                'targetGroupArn': context['target_group_arn'],
                'containerName': context['container_name'],
                'containerPort': 8000
            },
        ],
        desiredCount=3,
        launchType='EC2',
        role='ecsServiceRole',
        deploymentConfiguration={
            'maximumPercent': 200,
            'minimumHealthyPercent': 50
        },
        placementStrategy=[
            {
                'type': 'spread',
                'field': 'attribute:ecs.availability-zone'
            },
        ],
        healthCheckGracePeriodSeconds=123,
        schedulingStrategy='REPLICA',
        deploymentController={
            'type': 'ECS'
        }
    )
    print(response)
    #except Exception as e:
     #   print('exception in creating service:', type(e))


#update service
def update_service(root_para, context_para, task_def):
    ecs_client = boto3.client('ecs', region_name=root_para['aws_region'])
    #update service
    response=ecs_client.update_service(
        cluster=context_para['cluster_name'],
        service=context_para['ecs_service_name'],
        desiredCount=3,
        taskDefinition=task_def['taskDefinitionArn'],
        deploymentConfiguration={
            'maximumPercent': 200,
            'minimumHealthyPercent': 50
        },
        placementStrategy=[
            {
                'type': 'spread',
                'field': 'attribute:ecs.availability-zone'
            },
        ],
        forceNewDeployment=True,
        healthCheckGracePeriodSeconds=123
    )
    print(response)


#service controller
def cloud_native_controller(root_para, context_para):
    ecr_repo=root_para['ecr_repo_name'] #current build ecr repo
    current_context={}
    [current_context.update(context) for context in context_para if context['ecr_repo_name']==ecr_repo] #create current context para
    #print('current context', current_context)
    service_resp=describe_service(root_para, current_context) #describe service to check if first run or successive

    if len(service_resp['failures']) != 0: #create service route
        for failure in service_resp['failures']:
            if failure['reason'] == 'MISSING':
                print('service is missing')
                task_definition_status=register_task_definition(root_para, current_context)
                create_service(root_para, current_context, task_definition_status['taskDefinition'])    
                

    elif len(service_resp['services']) != 0: #update service route
        for service in service_resp['services']:
            if service['serviceName'] == current_context['ecs_service_name']:
                task_definition_status=register_task_definition(root_para, current_context)
                update_service(root_para, current_context, task_definition_status['taskDefinition'])



if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    parameter=fetch_parameter(para_name) #fetch execution parameter