import logging
import sys
import re
from my_colors import *
import builtins
class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
        self.original_stdout = sys.stdout  # Save reference to original stdout

    def write(self, buf):
        # Regular expression to match and remove ANSI escape codes
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        clean_buf = ansi_escape.sub('', buf)  # Remove ANSI codes
        for line in clean_buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
        self.original_stdout.write(buf)
    def flush(self):
        pass

#from logger import StreamToLogge
"""import sys
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    filename='error.log',
    filemode='a'
)

def fancy_print(message, log_level=logging.INFO, end='\n'):
    # Strip color codes for logging
    plain_message = re.sub(r'\033\[\d+m', '', message)
    logging.log(log_level, plain_message)

    # Print the message using the original print function with the specified 'end'
    original_print(message, end=end)
#
# Save the original print function
original_print = builtins.print




# Replace stdout with logging
#sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
# Now, both print statements and logging messages will go to the log file.
#print("This will go to the log file.")
#logging.info("This will also go to the log file.")

def main():
    download_speed = 0
    upload_speed = 0
    fancy_print(f"Download speed: {GREEN}{download_speed} Mbps{RESET} | Upload speed: {GREEN}{upload_speed} Mbps{RESET}", end ='\r')
    fancy_print(f"Download speed: {GREEN}{download_speed} Mbps{RESET} | Upload speed: {GREEN}{upload_speed} Mbps{RESET}", end ='\r')
    fancy_print(f"Download speed: {GREEN}{download_speed} Mbps{RESET} | Upload speed: {GREEN}{upload_speed} Mbps{RESET}", end ='\r')
    fancy_print(f"Download speed: {GREEN}{download_speed} Mbps{RESET} | Upload speed: {GREEN}{upload_speed} Mbps{RESET}", end ='\r')
if __name__ == '__main__':
    main()
"""





