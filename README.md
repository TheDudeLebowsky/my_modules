
# READ ME

Here are a few usefull modules

## my_nordvpn.py

- This modules allows to easily switch nord vpn server using subprocesses.
- It can be set up to use openVPN. In that case, unzip the file from ovpn_files folder #to be completed
- It also includes a few functions to help ensure that your identity is shielded.
- Can be easily used in within a loop where a new IP is required on each loop
- NOTE: because this modules will initiate and shut down processes for error handling (App not responding) it does require admin privilege to allow full functionality. Make sure to run vscode as admin. If not running as admin, NordVPN will not restart in case of unexpected error.
- Initiate with you personnal ip. This allows the script to ensure it is never exposed

Main functions:

- ip_status : returns your current status : Shield = 'current ip != personnal ip'. VPN = 'NordVPN run status'
- get_vpn_status : will verify if both nordvpn and its background process is running
- activate_identity_shielding : Ensures the vpn is running and activated. will start a thread to keep watching your IP. it can be set to either inform the user if IP is exposed or force shutdown the running script. (not recommended if you have opened files.)
- test_internet_speed(): Will verify your current internet speed. Can be usefull if you need to ensure a minimum speed before running a script
- test_connection_health(): Will ping a few server and verify the latency
- start,kill,restart : self-explanatory
- switch : function to use commands to switch vpn server

## my_logger.py

This simple module allows to easily replace the console print to logs

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:   %(message)s',
    filename='error.log',
    filemode='w'
)
logger = logging.getLogger('MyLogger')
stdout_logger = StreamToLogger(logger, logging.INFO)
sys.stdout = stdout_logger
lock = threading.Lock()
```

## my_colors.py

just a list of predefined color to use. includes a few function to demo the colors

- Import as a module: ```from colors import *```
- Demo functions have been commented out to avoid importing them.
