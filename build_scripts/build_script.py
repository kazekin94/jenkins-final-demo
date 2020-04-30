import boto3
import json
import docker
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
    actual_path=path_workspace.replace('<repo_name>', para['repo_name'])
    docker_file=actual_path+"/Dockerfile"
    print("Path to workspace:", docker_file)
    image_build_response=client.images.build(path=docker_file)
    print(image_build_response)
    

if __name__ == "__main__":
    #env variables
    para_name='django-helloworld'
    work_space_path='/home/ec2-user/workspace/<repo_name>'
    #set docker client
    docker_client=docker.from_env()
    #calls 
    fetch_para_response=fetch_parameter(para_name) #fetch para
    build_docker_image=build_image(docker_client, fetch_para_response, work_space_path) #build image