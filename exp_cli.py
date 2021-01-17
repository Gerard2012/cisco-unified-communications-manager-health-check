##############################################################################################
# modules
##############################################################################################

import paramiko
import datetime
from datetime import datetime
import re
import logging


##############################################################################################
# Functions
##############################################################################################

def parse_resp_exp(func):

    """
    Decorator function to parse th results of each command that is run in the server CLI.

    """

    def inner(*args,**kwargs):

        resp = str(func(*args,**kwargs)).replace("'b'", "").split('\\r\\n')

        return resp

    return inner


##############################################################################################
# Classes
##############################################################################################

class SSHConnectExp:

    """
    Creates an instance of the paramiko.SSHClient() class, and opens an SSH session to the server

        : param node : The hostname or IP of the UCM, IM&P or CUC server.
        : param username : username of the given server.
        : param password : password of the given server.

    """

    def __init__(self, node, username, password):
        self.node = node
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.node,username=self.username,password=self.password,timeout=60)
        self.conn = self.client.invoke_shell()


    def __repr__(self):
        return f'SSHConnect("{self.node}")'

    def __str__(self):
        return f'SSHConnect("{self.node}")'


    def init_connect(self):

        """
        Method to return the initial 'OK' prompt after an SSH session is opened.

        """

        logging.debug('## {} - {}.init_connect() -- ENTER'.format(__name__, self))

        try:
            def _init_connect(buffer=''):
                prompt = False
                output = self.conn.recv(65535)
                buffer += str(output)
                recursion_depth = 1
                max_recursion_depth = 10

                if 'OK' not in buffer and max_recursion_depth <= 10:
                    logging.debug('## {} - {}.init_connect() -- PROMPT == {}'.format(__name__, self, prompt))
                    recursion_depth += 1
                    return _init_connect(buffer)

                elif 'OK' not in buffer and max_recursion_depth > 10:
                    raise RecursionError('Too many loops.')

                elif 'OK' in buffer:
                    prompt = True
                    logging.debug('## {} - {}.init_connect() -- PROMPT == {}'.format(__name__, self, prompt))
                    return prompt

            return _init_connect()

        except Exception as e:
            logging.debug('## {} - {}.init_connect() -- EXCEPTION == {}'.format(__name__, self, e))
            return e


    @parse_resp_exp
    def run_cmd(self, cmd):

        """
        Runs a CLI command on the target server and confirms the return of the 'OK' prompt before completing.
        Decorated by the parse_resp() function to properly parse the return.

        """

        logging.debug('## {} - {}.run_cmd() -- ENTER'.format(__name__, self))

        try:
            self.conn.send(cmd + '\n')

            def _run_cmd(buffer=''):
                prompt = False
                output = self.conn.recv(65535)
                buffer += str(output)
                recursion_depth = 1
                max_recursion_depth = 10

                if 'OK' not in buffer and max_recursion_depth <= 10:
                    logging.debug('## {} - {}.run_cmd("{}") -- PROMPT == {}'.format(__name__, self, cmd, prompt))
                    return _run_cmd(buffer)

                elif 'OK' not in buffer and max_recursion_depth > 10:
                    raise RecursionError('Too many loops.')

                elif 'OK' in buffer:
                    prompt = True
                    logging.debug('## {} - {}.run_cmd("{}") -- PROMPT == {}'.format(__name__, self, cmd, prompt))
                    return buffer

            return _run_cmd()

        except Exception as e:
            logging.debug('## {} - {}.run_cmd("{}") -- EXCEPTION == {}'.format(__name__, self, cmd, e))
            return e


    def close_ssh(self):

        """
        Closes the SSH connection to the target server.

        """

        self.client.close()
        logging.debug('## {} - {}.close_ssh()'.format(__name__, self))


##############################################################################################
# Run
##############################################################################################

if __name__ == '__main__':

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG, datefmt="%H:%M:%S")

    pass
