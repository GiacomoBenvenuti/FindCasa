import requests

def get_current_ip():
    try:
        # Fetch the current public IP address
        response = requests.get("https://api.ipify.org")
        return response.text
    except requests.RequestException as e:
        print(f"Error occurred: {e}")
        return None


def confirm_ip(expected_ip:str="84.247.42.146"):

    current_ip = get_current_ip()

    if current_ip == expected_ip:
        print("IP checked!")
    else:
        raise ValueError(f"Expected IP not used: {current_ip}")
    
    return True
