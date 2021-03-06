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


#build image
def build_image(client, para, path_workspace):
    #build paths
    actual_path=path_workspace.replace('<pipeline_name>', para['pipeline_name']) #path to docker file
    docker_file=actual_path+"/Dockerfile" #path of dockerfile
    docker_file_path=os.path.dirname(docker_file) # os path
    #build repo name
    repo_name_template=para['image_repo_name']
    repo_name=repo_name_template.replace('<aws_account_id>', para['aws_account_id']).replace('<aws_region>', para['aws_region'])+'/'+para['image_name']
    image_name=repo_name+':'+para['image_tag']
    print('Image name:', image_name)
    #build image
    print('Image build started')
    try:
        image_build_response=client.images.build(path=docker_file_path, tag=image_name, dockerfile='Dockerfile') #returns image class obj, generator of json decoded logs
        print('Image built')
        return image_build_response
    except Exception as e:
        print('Exception in building image:', e)


#push image to ecr
def push_image(client, image_obj):
    ecr_client=boto3.client('ecr', region_name='ap-south-1')
    image_name=image_obj[0].tags[0] #expand image object to get built image tag, tag is object in image object
    print(image_name)
    try:
        #ecr authorization
        auth_resp=ecr_client.get_authorization_token()
        user, passwd=base64.b64decode(auth_resp['authorizationData'][0]['authorizationToken']).decode().split(':')
        registry=auth_resp['authorizationData'][0]['proxyEndpoint']
        login_resp=client.login(user, passwd, registry=registry) #login to repo
        print('Login succeded:', login_resp)
        auth_config={'username': user, 'password': passwd} #build creds for pushing image to ecr
        push_resp=client.images.push(image_name, auth_config=auth_config) #push image, via docker not ecs
        #print('Push response:', push_resp)
        print('Image pushed to ecr')
        auth_config['registry']=registry
        return auth_config
    except Exception as e:
        print("Exception raised in pushing image to ecr:", e)


'''
#update parameter
def update_para(para_name, para, ecr_auth):
    ssm_client=boto3.client('ssm', region_name=para['aws_region'])
    para['ecr_temp_auth']=ecr_auth
    response = ssm_client.put_parameter(
        Name=para_name,
        Value=json.dumps(para),
        Type='String',
        Overwrite=True,
        Tier='Standard'
    )
'''

    
if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetched_paras=fetch_parameter(para_name) #fetch para
    image_object=build_image(docker_client, fetched_paras, work_space_path) #build image
    ecr_auth=push_image(docker_client, image_object)  #push image
    #update_para(para_name, fetched_paras, ecr_auth)