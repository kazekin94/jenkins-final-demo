import boto3
import json
import docker
import os
from io import BytesIO


#fetch parameters from ssm
def fetch_parameter(para):
    #set ssm client
    ssm_client=boto3.client('ssm', region_name='ap-south-1')

    response = ssm_client.get_parameter(
        Name=para
    )
    para_value=response['Parameter']['Value']
    para_value_dict=json.loads(para_value)
    return para_value_dict


#build image
def build_image(client, para, path_workspace):
    print("Fetched para:", para)
    actual_path=path_workspace.replace('<pipeline_name>', para['pipeline_name']) #path to docker file
    print("Created path to workspace:", actual_path)
    docker_file=actual_path+"/Dockerfile" #path of dockerfile
    print("Path to dockerfile:", docker_file)
    docker_file_path=os.path.dirname(docker_file) # os path
    print("Path to docker build context:", docker_file_path)
    print("Start building image.")
    try:
        image_build_response=client.images.build(path=docker_file_path, tag=para['image_name'], dockerfile='Dockerfile') #returns image class obj, generator of json decoded logs
        image_id=image_build_response[0].id
        image_tags=image_build_response[0].tags
        print("Image id:", image_id, "Image tags:", image_tags)
    except Exception as e:
        print("Exception in building image:", e)
    return image_id, image_tags


#tag image
def tag_image(client, image_name, para):
    try:
        image_tag_template=para['image_tag']
        image_tag=image_tag_template.replace('<aws_account_id>', para['aws_account_id']).replace('<aws_region>', para['aws_region']).replace('<image_name>', image_name)
        print("Tag to be given to image:", image_tag)
        print("Old image name:", image_name)
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
    image_id, image_tag=build_image(docker_client, fetch_para_response, work_space_path) #build image
    call_tag_image=tag_image(docker_client, image_tag[0], fetch_para_response)
