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
    print(image_name)
    #build image
    print("Image build started")
    try:
        image_build_response=client.images.build(path=docker_file_path, tag=image_name, dockerfile='Dockerfile') #returns image class obj, generator of json decoded logs
        #print("Successful image built return object:", image_build_response)
        print("Image built")
        return image_build_response
    except Exception as e:
        print('Exception in building image:', e)


#push image to ecr
def push_image(image_obj):
    ecr_client=boto3.client('ecr', region_name='ap-south-1')
    print("Image object:", image_obj[0].tags)
    try:
        #ecr authorization
        auth_resp=ecr_client.get_authorization_token()
        decoded_auth=base64.b64decode(auth_resp['authorizationData'][0]['authorizationToken'])
        print(decoded_auth)
    except Exception as e:
        print("Exception raised in pushing image to ecr:", e)

    

if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetched_paras=fetch_parameter(para_name) #fetch para
    image_object=build_image(docker_client, fetched_paras, work_space_path) #build image
    ecr_push_image=push_image(image_object) 