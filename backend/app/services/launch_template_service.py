import boto3
import datetime
import re
from app.config.settings import AWS_REGION

ec2 = boto3.client("ec2", region_name=AWS_REGION)

SAFE_PATTERN = re.compile(r"^[a-zA-Z0-9\-_.]+$")


def sanitize(value, name="value"):
    """Sanitize input values to prevent injection attacks."""
    if not SAFE_PATTERN.match(value):
        raise ValueError(f"Invalid characters in {name}: {value}")
    return value


def update_launch_template_from_instance_tag(tag_value: str, lt_name: str):
    """
    Update launch template with AMI created from EC2 instance.
    
    Args:
        tag_value: The Name tag value of the EC2 instance
        lt_name: The name of the launch template to update
        
    Returns:
        dict: Result with success status and details
    """
    tag_value = sanitize(tag_value, "tag_value")
    lt_name = sanitize(lt_name, "launch_template_name")
    
    # Validate AWS credentials
    try:
        sts = boto3.client("sts", region_name=AWS_REGION)
        sts.get_caller_identity()
    except Exception as e:
        return {"success": False, "error": f"Invalid AWS credentials: {str(e)}"}


    # 1. Get EC2 instance by tag
    instances = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [tag_value]},
            {"Name": "instance-state-name", "Values": ["running", "stopped"]}
        ]
    )["Reservations"]

    if not instances:
        return {"success": False, "error": "No instance found with given tag"}

    instance = instances[0]["Instances"][0]
    instance_id = instance["InstanceId"]
    root_device = instance["RootDeviceName"]

    # 2. Create AMI with only root volume
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    ami_name = f"{tag_value}-ami-{timestamp}"
    ami_resp = ec2.create_image(
        InstanceId=instance_id,
        Name=ami_name,
        Description=f"AMI from {tag_value}",
        NoReboot=True,
        BlockDeviceMappings=[
            {
                "DeviceName": root_device,
                "Ebs": {"DeleteOnTermination": True}
            }
        ]
    )
    ami_id = ami_resp["ImageId"]

    # 3. Tag the AMI
    ec2.create_tags(
        Resources=[ami_id],
        Tags=[{"Key": "Name", "Value": "Test_AMI_V2"}]
    )

    # 4. Wait for the AMI to become available
    waiter = ec2.get_waiter("image_available")
    waiter.wait(ImageIds=[ami_id])

    # 5. Get snapshot ID from created AMI and tag it
    ami_info = ec2.describe_images(ImageIds=[ami_id])["Images"][0]
    snapshot_id = ami_info["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"]

    ec2.create_tags(
        Resources=[snapshot_id],
        Tags=[{"Key": "Name", "Value": "Test_AMI_V2_Volume"}]
    )

    # 6. Get launch template ID
    lt = ec2.describe_launch_templates(LaunchTemplateNames=[lt_name])
    lt_id = lt["LaunchTemplates"][0]["LaunchTemplateId"]

    # 7. Create new LT version using the AMI and set instance + volume tags
    version_resp = ec2.create_launch_template_version(
        LaunchTemplateId=lt_id,
        SourceVersion="$Latest",
        LaunchTemplateData={
            "ImageId": ami_id,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "Test-Server-Spot"}
                    ]
                },
                {
                    "ResourceType": "volume",
                    "Tags": [
                        {"Key": "Name", "Value": "Test-Server-Spot-Root"}
                    ]
                }
            ]
        }
    )
    new_version = version_resp["LaunchTemplateVersion"]["VersionNumber"]

    # 8. Set new version as default
    ec2.modify_launch_template(
        LaunchTemplateId=lt_id,
        DefaultVersion=str(new_version)
    )

    return {
        "success": True,
        "ami_id": ami_id,
        "launch_template_id": lt_id,
        "new_version": new_version
    }
