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
    print("Parameters fetched:", para_value_dict)
    return para_value_dict


#create deployment app if not available
def create_deployment_app(paras):
    client=boto3.client('codedeploy', region_name=paras['aws_region'])
    try:    #check if deployment app exists
        response=client.get_application(
            applicationName=paras['deployment_app_lift_shift']
        )
        print('Application {} already exists'.format(response['application']['applicationName']))
        return response['application']['applicationName'] #application name
    except Exception as e:
        if e.response['Error']['Code']=='ApplicationDoesNotExistException':  #application does not exist, create app, return name
            print('Application doesnt exist, creating')
            create_app_response=client.create_application(  
                applicationName=paras['deployment_app_lift_shift'],
                computePlatform='Server'
            )
            print("Application {} created".format(paras['deployment_app_lift_shift']))
            return paras['deployment_app_lift_shift'] #application name
        else:
            print('Unexpected error encountered:', e)


#list deployment groups
def list_deployment_groups(paras, app_name):
    client=boto3.client('codedeploy', region_name=paras['aws_region'])
    dgs=[] #list of deployment groups
    try:
        list_dg_resp=client.list_deployment_groups(
            applicationName=app_name
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
        if paras['dg_lift_shift'] not in dgs:
            dg_id=create_deployment_group(paras)
            print('dg didnt exist, created dg, dg id:', dg_id)
            return dg_id
        elif paras['dg_lift_shift'] in dgs:
            dg_id=get_deployment_group(paras)
            print('dg exists, dg id:', dg_id)
            return dg_id
    except Exception as e:
        print('Unexpected error occured:', e)


#create deployment group
def create_deployment_group(paras):
    client=boto3.client('codedeploy', region_name=paras['aws_region'])
    try:
        response=client.create_deployment_group(
            applicationName=paras['deployment_app_lift_shift'],
            deploymentGroupName=paras['dg_lift_shift'],
            autoScalingGroups=[paras['asg_lift_shift']],
            serviceRoleArn=paras['code_deploy_service_role'],
            deploymentStyle={'deploymentType': 'IN_PLACE', 'deploymentOption': 'WITHOUT_TRAFFIC_CONTROL'}
        )
        return response['deploymentGroupId']
    except Exception as e:
        print('Unexpected error occured while creating deployment group:', e)


#get deploment group
def get_deployment_group(paras):
    client=boto3.client('codedeploy', region_name=paras['aws_region'])
    response=client.get_deployment_group(
        applicationName=paras['deployment_app_lift_shift'],
        deploymentGroupName=paras['dg_lift_shift']
    )
    return response['deploymentGroupInfo']['deploymentGroupId']


#create deployment
def create_deployment(paras, dg_id):
    client=boto3.client('codedeploy', region_name=paras['aws_region'])
    response=client.create_deployment(
        applicationName=paras['deployment_app_lift_shift'],
        deploymentGroupName=dg_id,
        revision={
            'revisionType': 'S3',
            's3Location': {
                'bucket': paras['artifact_bucket_name'],
                'key': paras['s3_key'],
                'bundleType': 'zip'
            }
        }
    )
    print(response)


if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetched_paras=fetch_parameter(para_name) #fetch para
    app_name=create_deployment_app(fetched_paras) #create/fetch deployment application
    dg_id=list_deployment_groups(fetched_paras, app_name)
    deployment_id=create_deployment(fetched_paras, dg_id)