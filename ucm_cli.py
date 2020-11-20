##############################################################################################
# modules
##############################################################################################

import paramiko
import datetime
from datetime import datetime
import re
import logging

test_data = ['Unable to connect to Master Agent host: NYVMITEL01, Port: 4040. This may be due to Master or Local Agent being down.', 'drfCliMsg:  No history data is available']


##############################################################################################
# Functions
##############################################################################################

def parse_resp(func):

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

class SSHConnect:

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
        self.months = {
                'Jan': '01',
                'Feb': '02',
                'Mar': '03',
                'Apr': '04',
                'May': '05',
                'Jun': '06',
                'Jul': '07',
                'Aug': '08',
                'Sep': '09',
                'Oct': '10',
                'Nov': '11',
                'Dec': '12'
            }

    def __repr__(self):
        return f'SSHConnect("{self.node}")'

    def __str__(self):
        return f'SSHConnect("{self.node}")'


    def init_connect(self):

        """
        Method to return the initial 'admin:' prompt after an SSH session is opened.

        """

        logging.debug('## {} - {}.init_connect() -- ENTER'.format(__name__, self))

        try:
            def _init_connect(buffer=''):
                prompt = False
                output = self.conn.recv(65535)
                buffer += str(output)
                recursion_depth = 1
                max_recursion_depth = 10

                if 'admin:' not in buffer and max_recursion_depth <= 10:
                    logging.debug('## {} - {}.init_connect() -- PROMPT == {}'.format(__name__, self, prompt))
                    recursion_depth += 1
                    return _init_connect(buffer)

                elif 'admin:' not in buffer and max_recursion_depth > 10:
                    raise RecursionError('Too many loops.')

                elif 'admin:' in buffer:
                    prompt = True
                    logging.debug('## {} - {}.init_connect() -- PROMPT == {}'.format(__name__, self, prompt))
                    return prompt

            return _init_connect()

        except Exception as e:
            logging.debug('## {} - {}.init_connect() -- EXCEPTION == {}'.format(__name__, self, e))
            return e


    @parse_resp
    def run_cmd(self, cmd):

        """
        Runs a CLI command on the target server and confirms the return of the 'admin:' prompt before completing.
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

                if 'admin:' not in buffer and max_recursion_depth <= 10:
                    logging.debug('## {} - {}.run_cmd("{}") -- PROMPT == {}'.format(__name__, self, cmd, prompt))
                    return _run_cmd(buffer)

                elif 'admin:' not in buffer and max_recursion_depth > 10:
                    raise RecursionError('Too many loops.')

                elif 'admin:' in buffer:
                    prompt = True
                    logging.debug('## {} - {}.run_cmd("{}") -- PROMPT == {}'.format(__name__, self, cmd, prompt))
                    return buffer

            return _run_cmd()

        except Exception as e:
            logging.debug('## {} - {}.run_cmd("{}") -- EXCEPTION == {}'.format(__name__, self, cmd, e))
            return e


    def get_uptime(self):

        """
        Runs the 'show status' command on the target server and returns it's uptime.

        """

        resp = self.run_cmd('show status')
        logging.debug('## {} - {}.get_uptime() -- RESP == {}'.format(__name__, self, resp))
        uptime = resp[10].replace(',', '').split()[2]
        logging.debug('## {} - {}.get_uptime() -- UPTIME == {}'.format(__name__, self, uptime))
        unit = resp[10].replace(',', '').split()[3]
        logging.debug('## {} - {}.get_uptime() -- UNIT == {}'.format(__name__, self, unit))

        if unit != 'day' and unit != 'days' and unit != 'min':
            unit = 'hours'

        return uptime, unit


    def get_stopped_srvs(self):

        """
        Returns any stopped services on the target server.

        """

        ## A list of services that are usually disabled on subscriber nodes.
        ignore_list = [
            'Cisco CAR DB[STOPPED]  Commanded Out of Service', 
            'Cisco CAR Scheduler[STOPPED]  Commanded Out of Service', 
            'Cisco CDR Repository Manager[STOPPED]  Commanded Out of Service', 
            'Cisco DRF Master[STOPPED]  Commanded Out of Service', 
            'Cisco License Manager[STOPPED]  Commanded Out of Service', 
            'Cisco SOAP - CallRecord Service[STOPPED]  Commanded Out of Service',
            'Cisco Intercluster Lookup Service[STOPPED]  Commanded Out of Service',
            'Connection HTTPS Directory Feeder[STOPPED]  Commanded Out of Service'
            ]

        resp = self.run_cmd('utils service list')
        logging.debug('## {} - {}.get_stopped_srvs() -- RESP == {}'.format(__name__, self, resp))
        stopped_list = [elem for elem in resp if '[STOPPED]' in elem and 'Not Activated' not in elem]

        ## Compares the returned list of stopped services to the above list of services usually disbaled on subscriber nodes.
        for elem in ignore_list:
            if elem in stopped_list:
                stopped_list.remove(elem)

        logging.debug('## {} - {}.get_stopped_srvs() -- STOPPED SERVICES == {}'.format(__name__, self, stopped_list))

        return stopped_list


    def get_certs(self):

        """
        Returns the name, issuer, expiry date, and #days to expiry of each cert installed on the server.

        """

        resp = self.run_cmd('show cert list own')
        logging.debug('## {} - {}.get_certs() -- RESP == {}'.format(__name__, self, resp))
        cert_list = [elem.split(': ') for elem in resp if '.pem' in elem]

        ## Removes some unwanted text from the cert issuer details in each element of cert_list[].
        for elem in cert_list:
            if 'Certificate Signed by ' in elem[1]:
                elem[1] = re.sub('Certificate\ Signed\ by\ ', '', elem[1])
            elif 'Self-signed' in elem[1]:
                elem[1] = re.sub('\ certificate\ generated\ by\ system', '', elem[1])


        def _get_expire_date(elem):

            """
            Returns the expiry date of a cert.

                : param elem : an element from cert_list[].

            """

            cert_resp = self.run_cmd('show cert own ' + elem[0])
            logging.debug('## {} - {}._get_expire_date() -- CERT_RESP == {}'.format(__name__, self, cert_resp))
            for elem in cert_resp:
                if 'To:' in elem:
                    x = elem.split()
                    del x[0], x[0], x[2], x[2]

                    if x[0] in self.months: x[0] = self.months[x[0]]

                    date = str(x[1] + '/' + x[0] + '/' + x[2])
                    logging.debug('## {} - {}._get_expire_date() -- DATE == {}'.format(__name__, self, date))

                    return date


        def _expire_delta(elem):

            """
            Returns the number of days until a cert expires.

                : param elem : an element from cert_list[].

            """

            expire_date = datetime.strptime(elem[2], '%d/%m/%Y')
            today = datetime.now()
            delta = expire_date - today
            delta_days = delta.days
            logging.debug('## {} - {}._expire_delta() -- DELTA_DAYS == {}'.format(__name__, self, delta_days))

            return delta_days


        for elem in cert_list:
            elem.append(_get_expire_date(elem))

        for elem in cert_list:
            elem.append(_expire_delta(elem))

        logging.debug('## {} - {}.get_certs() -- CERT_LIST == {}'.format(__name__, self, cert_list))
        return cert_list


    def get_backup(self):


        """
        Returns the status of the last backup, the date of the last successful backup and the #days since a 
        successful backup of the target server.

        """

        resp = self.run_cmd('utils disaster_recovery history Backup')
        logging.debug('## {} - {}.get_backup() -- RESP == {}'.format(__name__, self, resp))
        backup_list = [elem for elem in resp if '.tar' in elem or 'TAR file not created' in elem]
        today = datetime.now()

        latest_backup_status = 'ERROR'

        if 'SUCCESS' in str(backup_list[-1]): latest_backup_status = 'SUCCESS'

        def _get_backup():

            latest_backup = str(backup_list.pop()).split()


            while 'SUCCESS' in latest_backup:
                latest_backup[3] = self.months[latest_backup[3]]
                last_successful_backup = str(latest_backup[4] + '/' + latest_backup[3] + '/' + latest_backup[7])
                last_successful_backup_strptime = datetime.strptime(last_successful_backup, '%d/%m/%Y')
                delta = today - last_successful_backup_strptime
                delta_days = delta.days

                logging.debug('## {} - {}.get_backup() -- RETURN == {}, {}, {}'.format(__name__, self, latest_backup_status, last_successful_backup, delta_days))
                return latest_backup_status, last_successful_backup, delta_days

            else:
                return _get_backup()


        return _get_backup()


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

    pass