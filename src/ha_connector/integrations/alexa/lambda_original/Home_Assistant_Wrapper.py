"""
Copyright 2019 Jason Hu <awaregit at gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os, json, logging, urllib3, configparser, boto3, traceback, base64, urllib

_debug = bool(os.environ.get('DEBUG'))

_logger = logging.getLogger('HomeAssistant-SmartHome')
_logger.setLevel(logging.DEBUG if _debug else logging.INFO)

# Initialize boto3 client at global scope for connection reuse
client = boto3.client('ssm')
app_config_path = os.environ['APP_CONFIG_PATH']
# Initialize app at global scope for reuse across invocations
app = None

class HA_Config:
    def __init__(self, config):
        """
        Construct new app with configuration
        :param config: application configuration
        """
        self.config = config

    def get_config(self):
        return self.config

def load_config(ssm_parameter_path):
    """
    Load configparser from config stored in SSM Parameter Store
    :param ssm_parameter_path: Path to app config in SSM Parameter Store
    :return: ConfigParser holding loaded config
    """
    configuration = configparser.ConfigParser()
    try:
        # Get all parameters for this app
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path,
            Recursive=False,
            WithDecryption=True
        )

        # Loop through the returned parameters and populate the ConfigParser
        if 'Parameters' in param_details and len(param_details.get('Parameters')) > 0:
            for param in param_details.get('Parameters'):
                param_path_array = param.get('Name').split("/")
                section_position = len(param_path_array) - 1
                section_name = param_path_array[section_position]
                config_values = json.loads(param.get('Value'))
                config_dict = {section_name: config_values}
                configuration.read_dict(config_dict)
    except BaseException as err:
        print("Encountered an error loading config from SSM.")
        print(str(err))
    finally:
        return configuration

def lambda_handler(event, context):
    global app
    
    _logger.debug('Event: %s', event)
    
    # Initialize app if it doesn't yet exist
    if app is None:
        print("Loading config and creating persistence object...")
        config = load_config(app_config_path)
        app = HA_Config(config)
    
    appConfig = app.get_config()['appConfig']
    
    destination_url = appConfig['HA_BASE_URL']
    cf_client_id = appConfig['CF_CLIENT_ID']
    cf_client_secret = appConfig['CF_CLIENT_SECRET']
    wrapper_secret = appConfig['WRAPPER_SECRET']

    assert destination_url is not None, 'Please set BASE_URL parameter'
    destination_url = destination_url.strip("/")

    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        timeout=urllib3.Timeout(connect=2.0, read=10.0)
    )
    
    req_body = base64.b64decode(event.get('body')) if event.get('isBase64Encoded') else event.get('body')
    
    _logger.debug(req_body)
    
    req_dict = urllib.parse.parse_qs(req_body)
    client_secret = req_dict[b'client_secret'][0].decode("utf-8")
    
    assert client_secret == wrapper_secret

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'CF-Access-Client-Id': cf_client_id,
        'CF-Access-Client-Secret': cf_client_secret
    }
    
    response = http.request(
        'POST', 
        '{}/auth/token'.format(destination_url),
        headers=headers,
        body=req_body
    )
    
    if response.status >= 400:
        _logger.debug("ERROR {} {}".format(response.status, response.data))
        return {
            'event': {
                'payload': {
                    'type': 'INVALID_AUTHORIZATION_CREDENTIAL' 
                            if response.status in (401, 403) else "INTERNAL_ERROR {}".format(response.status),
                    'message': response.data.decode("utf-8"),
                }
            }
        }
    _logger.debug('Response: %s', response.data.decode("utf-8"))
    return json.loads(response.data.decode('utf-8'))