import boto3
import json
import docker
import os
from io import BytesIO


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
    repo_name=repo_name_template.replace('<aws_account_id>', para['aws_account_id']).replace('<aws_region>', para['aws_region'])
    image_name=repo_name+'/'+para['image_name']+':'+para['image_tag']
    #build image
    print("Start building image.")
    try:
        image_build_response=client.images.build(path=docker_file_path, tag=image_name, dockerfile='Dockerfile') #returns image class obj, generator of json decoded logs
        return image_build_response
    except Exception as e:
        print("Exception in building image:", e)


#tag image
def tag_image(client, image_name, para, image_id):
    try:
        image_tag_template=para['image_tag']
        image_tag=image_tag_template.replace('<aws_account_id>', para['aws_account_id']).replace('<aws_region>', para['aws_region']).replace('<image_name>', image_name)
        print("Old image name:", image_name)
        print("Tag to be given to image:", image_tag)
        low_level_client=docker.APIClient(base_url='unix://var/run/docker.sock') #set low level client
        
        '''
        image_tag_response=client.tag(image_name,  tag=image_tag)     
        print("Tagging done?", image_tag_response)
        '''
    except Exception as e:
        print("Exception in tagging:", e)       


if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<pipeline_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetch_para_response=fetch_parameter(para_name) #fetch para
    image_object=build_image(docker_client, fetch_para_response, work_space_path) #build image
    #call_tag_image=tag_image(docker_client, image_tag[0], fetch_para_response, image_id)
