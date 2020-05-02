import boto3
import json
import os
import zipfile


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
    print("Parameters fetched:", para_value_dict)
    return para_value_dict


#zip files to make an archive
def put_s3(para, workspace_template):
    workspace_path=workspace_template.replace('<pipeline_name>', para['pipeline_name'])
    if os.path.exists(workspace_path):
        print("There")
    else:
        print("Not there")

 
#main function
if __name__ == "__main__":
    para_name='django-helloworld'    
    workspace_template='/home/ec2-user/workspace/<pipeline_name>'
    #calls
    fetched_paras=fetch_parameter(para_name)
    item_resp=put_s3(fetched_paras, workspace_template)
    