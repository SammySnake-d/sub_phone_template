import os
import yaml
from github import Github
import push  # 导入 push.py 中的类

def parse_gist_info(gist_link):
    """Parse username and gist ID from the Gist link."""
    parts = gist_link.split('/')
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    raise ValueError("Invalid GIST_LINK format")

def get_gist_content(g, username, gist_id):
    """Retrieve the content of the specified gist."""
    try:
        gist = g.get_gist(gist_id)
        print(f"Searching for clash.yaml in user {username}'s gist")

        for file in gist.files.values():
            print(f"Found file: {file.filename}")
            if file.filename == 'clash.yaml':
                return file.content
        return None
    except Exception as e:
        print(f"Error retrieving Gist content: {str(e)}")
        raise

def modify_yaml_content(content):
    """Modify the YAML content."""
    try:
        config = yaml.safe_load(content)
        print("Successfully loaded YAML content")

        direct_group = None
        select_group = None

        for group in config['proxy-groups']:
            if group['name'] == '🎯 全球直连':
                direct_group = group
                print("Found direct connection proxy group")
            elif group['name'] == '🔰 节点选择':
                select_group = group
                print("Found node selection proxy group")

        if direct_group and select_group:
            if '🔰 节点选择' not in direct_group['proxies']:
                direct_group['proxies'].append('🔰 节点选择')
                print("Added node selection to direct connection group")

            if '🎯 全球直连' in select_group['proxies']:
                select_group['proxies'].remove('🎯 全球直连')
                print("Removed direct connection from node selection group")

        return yaml.dump(config, allow_unicode=True, sort_keys=False)

    except Exception as e:
        print(f"Error modifying YAML content: {str(e)}")
        raise

def update_gist_content_via_push(token, username, gist_id, files):
    """Use PushToGist class from push.py to update Gist content."""
    try:
        push_client = push.PushToGist(token=token)

        # Ensure the filename is phone.yaml
        filename = "phone.yaml"  
        push_conf = {"username": username, "gistid": gist_id, "filename": filename}

        # Validate push_conf
        if not push_client.validate(push_conf):
            print(f"Invalid push configuration: {push_conf}")
            return False

        # Push the updated content
        success = push_client.push_to(content=files[filename]["content"], push_conf=push_conf, payload={"files": files}, group="collect")
        if success:
            print("Gist content updated successfully")
            return True
        else:
            print("Failed to update Gist content")
            return False
    except Exception as e:
        print(f"Error updating Gist content via PushToGist: {str(e)}")
        raise

def main():
    # Get configuration from environment variables
    source_gist_link = os.getenv('GIST_OLD_LINK')
    target_gist_link = os.getenv('GIST_LINK')
    # github_token = os.getenv('GIST_PAT')
    access_token = os.getenv('GIST_PAT')  # Access token for PushToGist

    try:
        print("Starting process...")

        # Parse the source and target Gist information
        source_username, source_gist_id = parse_gist_info(source_gist_link)
        target_username, target_gist_id = parse_gist_info(target_gist_link)

        print(f"Source Gist: {source_username}/{source_gist_id}")
        print(f"Target Gist: {target_username}/{target_gist_id}")

        # Initialize GitHub client
        g = Github(access_token)

        # Retrieve source Gist content
        print("Retrieving source Gist content...")
        content = get_gist_content(g, source_username, source_gist_id)
        if not content:
            raise Exception("clash.yaml file not found")

        # Modify YAML content
        print("Modifying YAML content...")
        modified_content = modify_yaml_content(content)
        if not modified_content:
            raise Exception("Failed to modify YAML content")

        # Prepare files for updating the target Gist with filename "phone.yaml"
        files = {
            "phone.yaml": {
                "content": modified_content
            }
        }

        # Update target Gist using PushToGist class
        print("Updating target Gist...")
        success = update_gist_content_via_push(access_token, target_username, target_gist_id, files)
        if not success:
            raise Exception("Failed to update Gist content")
        else:
            print("Successfully updated YAML configuration")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
