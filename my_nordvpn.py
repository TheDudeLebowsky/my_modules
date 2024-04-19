
import subprocess
import time
import requests
import threading
import logging
import sys
import speedtest
from bs4 import BeautifulSoup
import random
import threading
import os
from pythonping import ping
from requests.exceptions import SSLError, RequestException
import ctypes

from my_colors import *
from my_logger import StreamToLogger

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s:%(levelname)s:   %(message)s',
    filename='error.log',
    filemode='w'
)
logger = logging.getLogger('MyLogger')
stdout_logger = StreamToLogger(logger, logging.INFO)
sys.stdout = stdout_logger
lock = threading.Lock()






def cls():
    if os.name == 'nt':
        os.system('cls')





class VPNManager():
    def __init__(self, country = 'United States', personnal_ip='10.0.0.0', use_openvpn=False, use_identity_shield=False, force_vpn=False):





        #OPTIONS
        self.debug_mode = False
        self.rate_limit_delay = 1
        self.max_threads = 20
        self.max_retry = 5
        self.speed_threshold = 200
        self.vpn_wait_time = 25
        #self.is_admin()



        #DO NOT MODIFY
        self.vpn_country = country
        self.vpn_provider = 'NordVPN' if use_openvpn == False else 'OpenVPN'
        self.personnal_ip = personnal_ip
        self.masked_personnal_ip = self.mask_ip(self.personnal_ip)
        self.kill_command = r"taskkill /F /IM "
        self.shield_status = False
        self.pause_shielding = False
        self.vpnconfig_path = 'ovpn_files'

        self.force_vpn = force_vpn
        self.test_servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
        self.ip_check_interval = 10
        self.ping_count = 5
        self.test_timeout = 2

        self.use_identity_shield = use_identity_shield
        if self.use_identity_shield == True:
            self.identity_shield_activate()

        if use_openvpn == True:
            self.openvpn_mode = 'tcp' #tcp or udp
            self.openvpn_command_path = r"C:\Program Files\OpenVPN\bin\openvpn-gui.exe"
            self.openvpn_country_code, self.openvpn_server_ids = self.get_country_data(self.vpn_country)
            self.openvpn_executables = [
                {'Exec': 'openvpn.exe', 'Status': False, 'Type': 'Task', 'ServiceName' : None},
                {'Exec': 'openvpn-gui.exe', 'Status': False, 'Type': 'Task', 'ServiceName' : None},
                {'Exec': 'openvpnserv.exe', 'Status': False, 'Type': 'Service', 'ServiceName' : 'OpenVPNService'},
                {'Exec': 'openvpnserv2.exe', 'Status': False, 'Type': 'Service', 'ServiceName' : 'OpenVPNServiceInteractive'},]

        self.nordvpnpath = r"C:\Program Files\NordVPN\NordVPN.exe"
        self.nordvpn_service_path = r"C:\Program Files\NordVPN\nordvpn-service.exe"
        self.nordvpn_serverlist_url = 'https://nordvpn.com/ovpn/?_gl=1*1jwic4v*_ga*MTMyMzk5MDYxOS4xNzAzMDQ1ODI2*_ga_LEXMJ1N516*MTcwNTAyMDAyNi4zLjEuMTcwNTAyMTMwNy4xMS4wLjA.*_gcl_au*NTMwNzM5MDgwLjE3MDMwNDU4MjY.*FPAU*NTMwNzM5MDgwLjE3MDMwNDU4MjY.&_ga=2.249249935.90411397.1705020026-1323990619.1703045826'
        self.nordvpn_executables = [
            {'Exec': 'nordvpn-service.exe', 'Status': False, 'Type': 'Service', 'ServiceName' : 'nordvpn-service'},
            {'Exec': 'NordVPN.exe', 'Status': False, 'Type': 'Task', 'ServiceName' : None}, ]
        self.nordvpn_switch_command = f'"{self.nordvpnpath}" -c -g {self.vpn_country}'
        self.get_vpn_status(self.nordvpn_executables, use_print=False)
        self.current_ip = self.ip_status()
        self.masked_current_ip = self.mask_ip(self.personnal_ip)





#Command construction
    def construct_kill_command(self, executable, executable_type):
        if executable_type == 'Task':
            command = f"{self.kill_command} {executable}"
        elif executable_type == 'Service':
            command = f"net stop {executable}"
        else:
            raise ValueError("Invalid executable type")
        print(f"Command : {INFO}{command}{RESET}")
        return command

    def construct_launch_command(self, executable_type):
        if executable_type == 'Task':
            command =f'"{self.nordvpnpath}" -c -g {self.vpn_country}'
        elif executable_type == 'Service':
            command = f'"{self.nordvpn_service_path}"'
        else:
            raise ValueError("Invalid executable type")
        print(f"Command : {INFO}{command}{RESET}")
        return command

    def construct_openvpn_launch_command(self, vpn_country=None):
        if vpn_country is None:
            vpn_country = self.vpn_country
        port = '1194' if self.openvpn_mode == 'udp' else '443'
        server_id = random.choice(self.openvpn_server_ids)
        self.openvpn_config_file = f"{self.openvpn_country_code}{server_id}.nordvpn.com.{self.openvpn_mode}{port}.ovpn"
        command = rf'"{self.openvpn_command_path}" --config C:\Program Files\OpenVPN\config\{self.openvpn_config_file}'
        print(f"Command : {INFO}{command}{RESET}")

        return command


#OpenVPN functions
    def get_ovpn_files(self, url=None, download_folder=None, rate_limit_delay=None, max_threads=None):

        """Used to download all ovpn config files from nordvpn. """
        """You only need to run this once to download all the files."""
        """You might need to redownload the files from time to time to get the latest servers."""
        """Check https://support.nordvpn.com/General-info/1086573432/How-to-find-various-configuration-files.htm"""
        if url is None:
            url = self.nordvpn_serverlist_url
        if download_folder is None:
            download_folder = self.vpnconfig_path
        if max_threads is None:
            max_threads = self.max_threads
        if rate_limit_delay is None:
            rate_limit_delay = self.rate_limit_delay




        def download_file(url, local_filename, rate_limit_delay):
            try:
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    time.sleep(rate_limit_delay)  # Delay to handle rate limiting
                print(f"Downloaded {local_filename}")
            except requests.RequestException as e:
                print(f"Error downloading {local_filename}: {e}")





        try:
            response = requests.get(url)
            response.raise_for_status()  # will throw an error for failed requests
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a')

            if not os.path.exists(download_folder):
                os.makedirs(download_folder)

            threads = []
            for link in links:
                href = link.get('href')
                if href and href.endswith('.ovpn'):
                    local_filename = os.path.join(download_folder, href.split('/')[-1])
                    if not os.path.exists(local_filename):
                        download_link = href if href.startswith('http') else url + href
                        t = threading.Thread(target=download_file, args=(download_link, local_filename, rate_limit_delay))
                        threads.append(t)
                        t.start()

                        if len(threads) >= max_threads:
                            for t in threads:
                                t.join()  # Wait for the threads to finish
                            threads = []  # Reset the thread list
                    else:
                        print(f"Skipped: {local_filename}")

            # Wait for any remaining threads to finish
            for t in threads:
                t.join()

        except requests.RequestException as e:
            print(f"Error: {e}")

    def get_country_data(self, country_name):
        file_path = os.path.join(self.ovpnconfig_path, 'zz_COUNTRY_CODES.txt')
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Variables to store country code and server IDs
        country_code = None
        server_ids = None

        # Flag to indicate if the required country block is being read
        reading_country = False

        for line in lines:
            if "country = '" + country_name + "'" in line:
                reading_country = True
            elif reading_country and "country_code = '" in line:
                country_code = line.split("'")[1]  # Extract country code
            elif reading_country and "server_id = " in line:
                server_ids = eval(line.split("= ")[1])  # Extract and convert server IDs
                break  # Exit loop after finding server IDs

        return country_code, server_ids





#//Helper functions

    def mask_ip(self, ip=None):
        if ip is None:
            ip = self.personnal_ip
        return "**.**.***.*" + ip[-2:]

    def conditional_coloring(self, value, expected_value=None, lower_is_better=False, boolean=False):


        success = False
        if boolean == True:
            expected_value = True
            if value == expected_value:
                color = SUCCESS
                success = True
            else:
                color = ERROR
            return color, success

        if expected_value is None:
            expected_value = self.speed_threshold

        # Define rating thresholds
        if lower_is_better:
            rating_a = expected_value * 0.75
            rating_b = expected_value * 0.9
            rating_c = expected_value
            rating_d = expected_value * 1.25
        else:
            rating_d = expected_value / 3
            rating_c = expected_value / 2
            rating_b = expected_value / 1.5
            rating_a = expected_value



        if lower_is_better:
            if value <= rating_a:
                color = SUCCESS
                success = True
            elif value <= rating_b:
                color = CYAN
            elif value <= rating_c:
                color = YELLOW
            elif value <= rating_d:
                color = ORANGE
            else:
                color = RED
        else:
            if value >= rating_a:
                color = SUCCESS
                success = True
            elif value >= rating_b:
                color = CYAN
            elif value >= rating_c:
                color = YELLOW
            elif value >= rating_d:
                color = ORANGE
            else:
                color = RED

        return color, success

    def is_admin(self):
        elevated_status = ctypes.windll.shell32.IsUserAnAdmin()
        if elevated_status:
            return
        else:
            # Re-run the program with admin rights and exit the current instance
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

            print(f"Admin rights acquired")
            time.sleep(10)



#//MAIN FUNCTIONS
#Process management
    def start(self, executables=None, restarting=False):
        print(f"\n{FOCUS}---> STARTING VPN EXECUTABLE. <---{RESET}") if restarting == False else None
        if executables is None:
            executables = self.nordvpn_executables

        retry = 0
        max_retry = self.max_retry

        # VPN launching function
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0

        if self.vpn_status and self.shield_status:
            print(f"{SUCCESS}VPN is already activated{RESET}")
            return

        if self.vpn_status and not self.shield_status:
            print(f"shield status={INFO}{self.shield_status}{RESET}")
            print(f"VPN status={INFO}{self.vpn_status}{RESET}")
            self.kill()

        while retry < max_retry:
            for executable_dict in executables:
                if executable_dict['Status'] == False:  # Check if executable's Status is True

                    executable_type = executable_dict['Type']
                    command = self.construct_launch_command(executable_type)


                    process = subprocess.Popen(command, shell=True, creationflags=creation_flags)




                    time.sleep(self.vpn_wait_time)
                    self.ip_status()
                    self.get_vpn_status(use_print=True)

                    if self.vpn_status and self.shield_status:
                        print(f'{SUCCESS}VPN LAUNCHED SUCCESSFULLY{RESET}')
                        return

            retry += 1
            print(f'{ERROR}VPN LAUNCH FAILED.{RESET}RETRYING... {INFO}({retry}/{max_retry}){RESET}')
            if retry >= max_retry:
                print(f'{ERROR}VPN LAUNCH FAILED... {RESET}Shit happens...')
                input(f"Press any key to exit...")
                exit()

        return

    def kill(self, executables=None, restarting=False):
        print(f"\n{FOCUS}---> KILLING VPN PROCESSES <---{RESET}") if restarting==False else None
        if executables is None:
            executables = self.nordvpn_executables
            #print(executables)
            for executable in executables:
                #print(executable['Status'])
                #print(executable['Exec'])
                #print(executable['Type'])
                #print(executable['ServiceName'])
                pass
        if self.vpn_status == False:
            print(f"{WARNING}No Process to kill{RESET}")
            return
        retry = 0
        max_retry = self.max_retry



        while retry < max_retry:
            for executable_dict in executables:
                if executable_dict['Status']:  # Check if executable's Status is True

                    executable = executable_dict['Exec']
                    executable_type = executable_dict['Type']
                    if executable_type == 'Service':
                        executable = executable_dict['ServiceName']
                    command = self.construct_kill_command(executable, executable_type)
                    print(f'{MY_RED}KILLING{RESET} {FOCUS}{executable}{RESET}. Please wait...')
                    try:
                        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                        stdout, stderr = process.communicate(timeout=60)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        stdout, stderr = process.communicate()
                        print("Process timed out and was killed")
                    #logger.info("Standard Output:", stdout)
                    #logger.info("Standard Error:", stderr)
                    time.sleep(self.vpn_wait_time)
                    self.get_vpn_status()

            if not self.vpn_status:  # Check overall VPN status
                print(f'{MY_GREEN}---> VPN KILLED SUCCESSFULLY <---{RESET}')
                retry = 0
                return
            else:
                retry += 1
                print(f'{ERROR}VPN KILL FAILED, RETRYING ({INFO}{retry}/{max_retry}{RESET})')
                if retry >= max_retry:
                    print(f'{MY_RED}VPN KILL FAILED... Shit happens...{RESET}')
                    input("Press any key to continue... ")
                    exit()


        retry = 0
        return

    def restart(self):
        print(f"\n{FOCUS}---> RESTARTING VPN <---{RESET}")
        self.kill(restarting=True)
        self.start(restarting=True)

    def switch(self, command=None):
        if command is None:
            command = self.nordvpn_switch_command
        self.pause_shielding = True

        retry = 0
        max_retry = self.max_retry


        while retry < max_retry:
            current_ip = self.current_ip
            masked_current_ip = self.mask_ip(current_ip)
            print(f"{FOCUS}---> SWITCHING VPN SERVER. <---{RESET}")
            print(f"Current IP : {INFO}{masked_current_ip}{RESET} ---> {INFO}{self.vpn_country}{RESET}")
            print(f"Command : {INFO}{command}{RESET}")
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            time.sleep(self.vpn_wait_time)
            new_ip = self.ip_status()
            masked_new_ip = self.mask_ip(new_ip)
            print(f'SWITCHING TO {INFO}{masked_new_ip}{RESET}')

            if new_ip != current_ip and new_ip is not None:
                print(f'{MY_BRIGHT_GREEN}---> VPN SWITCHED SUCCESSFULLY <---{RESET}')
                self.pause_shielding = False

                break
            else:
                retry += 1
                print(f'{ERROR}VPN SWITCH FAILED, RETRYING ({ERROR}{retry}{RESET}/{ERROR}{self.max_retry}{RESET})')
                if retry >= self.max_retry:
                    print(f'{ERROR}VPN SWITCH FAILED... {RESET}Please check internet connection')
                    if self.force_vpn == True:
                        self.restart()
                    else:
                        input(f"Press any key to continue... ")
                    retry = 0
        retry = 0
        self.pause_shielding = False
        return new_ip




#Shielding thread
    def identity_shield(self, instant_shutdown):
        """To use with thread to ensure identity shield is always on"""
        """Will exit if exposed"""

        while not self.shutdown_event.is_set():
            if self.pause_shielding == False:
                self.ip_status(use_print=False)
                self.get_vpn_status(use_print=False)
                if self.shield_status == False:
                    print(f"{MY_RED}\nYOUR IDENTITY IS EXPOSED.{RESET} Exiting...")
                    self.shutdown_event.set()

                else:
                    time.sleep(self.ip_check_interval)


        if self.shutdown_event.is_set():
            if instant_shutdown == True:
                print(f"{MY_RED}SHUTTING DOWN...{RESET}")
                os._exit(0)
            else:
                print(f"{MY_RED}SHUTTING DOWN ON NEXT CHECKPOINT...{RESET}")

    def identity_shield_activate(self, country=None, instant_shutdown=False):
        if country is None:
            country = self.vpn_country
        else:
            self.vpn_country = country
        print(f"\n{TITLE}{BOLD}===> ACTIVATING IDENTITY SHIELDING <==={RESET}")

        self.ip_status()
        self.get_vpn_status()
        if self.shield_status == True and self.vpn_status == True:
            print(f"---> YOUR IDENTITY IS {MY_BRIGHT_GREEN}SHIELDED.{RESET} <--- ")
            print(f"Current IP : {INFO}{self.masked_current_ip}{RESET}")
            print(f"{SUBDIVIER}")
            time.sleep(1)



        elif self.shield_status == False or self.vpn_status == False:
            print(f"YOUR IDENTITY IS {MY_RED}EXPOSED.{RESET} Current IP : {INFO}{self.masked_current_ip}{RESET} Attempting to start VPN")
            while True:
                self.start()
                self.get_vpn_status()
                self.ip_status()
                print(self.shield_status, self.vpn_status)
                if self.shield_status == True and self.vpn_status == True:
                    break


            print(f"Current IP : {INFO}{self.masked_current_ip}{RESET} | Process : {INFO}{self.vpn_provider}{RESET} is running")
            print(f"{MY_BRIGHT_GREEN}===> YOUR IDENTITY IS SHIELDED. <==={RESET}")
            print(f"{SUBDIVIER}")
            time.sleep(2)
        self.shutdown_event = threading.Event()
        self.vpn_check_thread = threading.Thread(target=self.identity_shield, args=(instant_shutdown, ))
        self.vpn_check_thread.start()

        return


#Internet health check
    def check_connection_health(self):
        health_results = {}
        print(f"\n{FOCUS}---> TESTING CONNECTION HEALTH <---{RESET}")

        for server in self.test_servers:
            response_list = ping(server, count=self.ping_count, timeout=self.test_timeout)
            success_count = sum(1 for response in response_list if response.success)

            # Check if there are successful pings
            if success_count > 0:
                success_rate = (success_count / self.ping_count) * 100
                average_latency = sum(response.time_elapsed_ms for response in response_list if response.success) / success_count
            else:
                success_rate = 0
                average_latency = float('inf')  # Indicates no response
            success_rate_color= self.conditional_coloring(success_rate, 100)[0]
            average_latency_color= self.conditional_coloring(average_latency, 60, lower_is_better=True)[0]
            health_results[server] = {
                "Success Rate": f"{success_rate_color}{success_rate}{RESET} %",
                "Average Latency": f"{average_latency_color}{round(average_latency, 2)}{RESET} ms"
            }

        # Print the health results for each server
        for server, health in health_results.items():
            print(f"Server: {MY_BLUE}{server}{RESET}")
            for key, value in health.items():
                print(f"  {key} : {value}")

        return health_results

    def test_internet_speed(self, min_speed=None):
        print(f"\n{FOCUS}---> TESTING INTERNET SPEED <---{RESET}")

        if min_speed is None:
            min_speed = self.speed_threshold
        download_speed = 0
        upload_speed = 0
        retry = 0
        max_retry = self.max_retry
        success = False

        while success == False:

            try:
                st = speedtest.Speedtest()
                st.get_best_server()  # This finds the best server for the speed test
                # Perform the speed test
                download_speed = st.download() / 1_000_000  # Convert from bits/s to Mbps
                upload_speed = st.upload() / 1_000_000  # Convert from bits/s to Mbps
                color, success = self.conditional_coloring(download_speed)
                download_speed = f"{download_speed:.2f}"
                upload_speed = f"{upload_speed:.2f}"
                print(f"Download speed: {color}{download_speed} Mbps{RESET} | Upload speed: {color}{upload_speed} Mbps{RESET} | Attempt #{INFO}{retry+1}/{max_retry}{RESET}")
                time.sleep(1)
                if success == True:
                    break
                else:
                    time.sleep(self.vpn_wait_time)
                    retry += 1

            except Exception as e:
                error_message = str(e)
                if 'unable to connect' in error_message.lower():
                    print(f"Error: Unable to connect to, maybe check your internet connection")
                else:
                    print(f'An error occurred: {ERROR}{e}{RESET}')
                retry += 1
                time.sleep(self.vpn_wait_time)
            if retry >= max_retry:
                print(f'{ERROR}Exceeded max retry.{retry}/{max_retry}{RESET}')
                if self.force_vpn == True and self.vpn_status == True:
                    self.switch()
                else:
                    input(f"Press any key to exit... ")
                    exit()
                retry = 0



        retry = 0
        return download_speed, upload_speed

    def ip_status(self, use_print=True):
        """Prints the current IP address"""
        retry = 0
        print(f"\n{FOCUS}---> GETTING IP INFO. <---{RESET}") if use_print else None
        max_retry = self.max_retry
        ip_address = None
        while retry < max_retry:
            try:
                response = requests.get('https://api.ipify.org')
                if response.status_code == 200:
                    ip_address = response.text.strip()
                    self.current_ip = ip_address
                    self.masked_current_ip = self.mask_ip(ip_address)
                    break
                else:
                    retry += 1
                    print(f"{ERROR}ERROR : {response.status_code}{RESET} Retrying : {retry}/{max_retry}") if use_print else None

            except SSLError as e:
                print(f"SSL error occurred: {e} Retrying : {retry}/{max_retry}") if use_print else None
                retry += 1

            except RequestException as e:
                print(f"{ERROR}An error occurred: {e}{RESET}") if use_print else None
                retry += 1
                if "NameResolutionError" in str(e):
                    print(f"{ERROR}DNS resolution failed for api.ipify.org {RESET} Retrying : {retry}/{max_retry}") if use_print else None



            except Exception as e:
                print(f"{ERROR}An error occurred: {e}{RESET}") if use_print else None
                retry += 1
            if retry >= max_retry:
                print(f"{ERROR}ERROR : COULD NOT FETCH CURRENT IP ADDRESS. Please check your connection.{RESET}") if use_print else None
                if self.force_vpn == True:
                    self.switch()
                else:
                    input(f"Press any key to continue... ")
                retry = 0
            time.sleep(5)

        if self.current_ip == self.personnal_ip:
            self.shield_status = False
        else:
            self.shield_status = True
        retry = 0
        if use_print == True:
            color_shield, success = self.conditional_coloring(self.shield_status, boolean=True)
            color_vpn_status, success = self.conditional_coloring(self.vpn_status, boolean=True)
            print(f"Current IP : {INFO}{self.masked_current_ip}{RESET}, Personal IP : {INFO}{self.masked_personnal_ip}{RESET} | Status : Shield = {color_shield}{self.shield_status}{RESET} VPN = {color_vpn_status}{self.vpn_status}{RESET}") if use_print else None
        return ip_address

    def get_vpn_status(self, executables=None, use_print=True):
        print(f"\n{BOLD}---> GETTING CURRENT STATUS. <---{RESET}") if use_print else None
        """Checks if the specified executables are running."""
        if executables is None:
            executables = self.nordvpn_executables


        try:
            process = subprocess.Popen('tasklist', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=60)
            logger.info("Standard Output:", stdout)
            logger.info("Standard Error:", stderr)
            logger.info("Process timed out and was killed")
        # Check the status of each executable
        for executable_dict in executables:
            executable = executable_dict['Exec']
            executable_dict['Status'] = executable in stdout
            if use_print:
                color, success = self.conditional_coloring(executable_dict['Status'], boolean=True)
                status_text = f"{color}RUNNING{RESET}" if executable_dict['Status'] else f"{color}NOT RUNNING{RESET}"
                print(f"{INFO}{executable}{RESET} status: {INFO}{status_text}{RESET}") if use_print else None

        self.vpn_status = all(exec['Status'] for exec in executables)
        return executables



def demo():
    vpn = VPNManager(country = 'United States', personnal_ip='10.0.0.0', use_openvpn=False, use_identity_shield=False, force_vpn=False)
    vpn.identity_shield_activate()
    vpn.get_vpn_status()
    vpn.ip_status()

    count =1
    while True:
        print(f"{MY_TEAL}{BOLD}===>{RESET} {TITLE}LOOP #{count}{RESET} {MY_TEAL}<==={RESET}")
        vpn.get_vpn_status()
        vpn.test_internet_speed()
        vpn.check_connection_health()
        count+=1
        if count == 5:

            vpn.kill()
        if count == 7:

            vpn.start()
        if count >= 10:

            vpn.switch()
            time.sleep(60)
        if count == 15:

            vpn.restart()
        if count ==25:
            vpn.kill()














if __name__ == "__main__":
    demo()








