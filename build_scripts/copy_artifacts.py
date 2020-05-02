import boto3
import json
import os
import string
import zipfile
import random


#fetch para from para store
def fetch_parameter(para):
    #set ssm client
    print("Fetching paras from parameter store.")
    ssm_client=boto3.client('ssm', region_name='ap-south-1')

    response = ssm_client.get_parameter(
        Name=para
    )
    para_value=response['Parameter']['Value']
    para_value_dict=json.loads(para_value)
    return para_value_dict


#zip files to make an archive
def put_s3(para, workspace_template):
    workspace_path=workspace_template.replace('<pipeline_name>', para['pipeline_name']) #workspace path
    print("Workspace path:", workspace_path)
    letter_choice=string.ascii_lowercase+string.ascii_uppercase #set random letters
    random_word=''.join(random.choice(letter_choice) for i in range (10)) #generate 10 letter random letter
    zip_filename=random_word+'-artifact.zip'
    print('Zip filename', zip_filename)
    if os.path.exists(workspace_path):
        print('Workspace exists in slave instance')
        print('Creating archive to send to s3')
        filepaths=[] #all filepaths in build script dir 
        for root, directories, files in os.walk(workspace_path+'/build_scripts'):
            for filename in files:
                filepath = os.path.join(root, filename)
                filepaths.append(filepath)
        #filepaths=filepaths.append(workspace_path+'/appspec.yml')
        appspec_path=workspace_path+'/appspec.yml'
        print(appspec_path)
        filepaths.append(appspec_path)
        print('Filepaths in buildscripts directory:', filepaths)
        
    else:
        print('Not there')

 
#main function
if __name__ == "__main__":
    para_name='django-helloworld'    
    workspace_template='/home/ec2-user/workspace/<pipeline_name>'
    #calls
    fetched_paras=fetch_parameter(para_name)
    item_resp=put_s3(fetched_paras, workspace_template)
    