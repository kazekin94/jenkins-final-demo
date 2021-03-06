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
    #check if workspace path exists
    if os.path.exists(workspace_path):
        print('Workspace exists in slave instance')
        print('Creating archive to upload to s3')
        filepaths=[] #store filepaths in build script dir 
        for root, directories, files in os.walk(workspace_path+'/build_scripts'):
            for filename in files:
                filepath = os.path.join(root, filename)
                filepaths.append(filepath)
        appspec_path=workspace_path+'/appspec.yml'
        filepaths.append(appspec_path) #files to append
        #begin zip
        zip_file=zipfile.ZipFile(zip_filename, 'w')
        with zip_file:
            for file in filepaths:
                print('Zipping:', file.split('/home/ec2-user/workspace/python-pipeline/')[1])
                zip_file.write(file, file.split('/home/ec2-user/workspace/python-pipeline/')[1], compress_type=zipfile.ZIP_DEFLATED)
        #check if zip exists
        if os.path.exists(workspace_path+'/'+zip_filename):
            s3_client = boto3.client('s3', region_name=para['aws_region']) #obj exists, put to s3
            stream_body=open(workspace_path+'/'+zip_filename, 'rb')
            s3_key=zip_filename
            print('Putting artifact to s3')
            s3_client.put_object(
                Bucket=para['artifact_bucket_name'],
                Body=stream_body,
                Key=s3_key
            )
            os.remove(s3_key) #delete artifact from workspace
            print('Artifact removed from workspace:', s3_key)
            return s3_key
        else:
            print('Zip doesnt exist')
    else:
        print('Not there')


#update parameter
def update_para(para_name, para, key):
    ssm_client=boto3.client('ssm', region_name=para['aws_region'])
    para['s3_key']=key
    response = ssm_client.put_parameter(
        Name=para_name,
        Value=json.dumps(para),
        Type='String',
        Overwrite=True,
        Tier='Standard'
    )


#main function
if __name__ == "__main__":
    para_name='django-helloworld'    
    workspace_template='/home/ec2-user/workspace/<pipeline_name>'
    #calls
    fetched_paras=fetch_parameter(para_name)
    s3_key=put_s3(fetched_paras, workspace_template)
    update_para(para_name, fetched_paras, s3_key)
    