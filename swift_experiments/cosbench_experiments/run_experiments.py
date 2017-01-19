import sys
from subprocess import Popen, PIPE
import subprocess
from os import listdir
import os
import paramiko
from ConfigParser import SafeConfigParser
import time
import shutil
import xml.etree.ElementTree as ET
import select

SWIFT_CONF_DIR = "swift_conf"

class SwiftNodeSSH:
    ip = ""
    ssh = ""
    username = ""
    password = ""

    def __init__(self):
        self.ip = ip
        self.ssh = paramiko.SSHClient()
        self.username = username
        self.password = password
        self.sudo_command = "echo " + self.password + " | sudo -S"

    def connect(self):
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip,
                         username=self.username,
                         password=self.password)
        except paramiko.AuthenticationException:
            print("Authentication failed when connecting to %s" % self.ip)
            exit(1)
        except:
            print("Could not SSH to %s" % self.ip)

    def exec_ssh(self, *args, **kwargs):
        command = kwargs.get("command", None)
        if command:
            print("Command: %s" % command),
            stdin, stdout, stderr = self.ssh.exec_command(command)
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
                    if len(rl) > 0:
                        print stdout.channel.recv(1024)
            if stdout and stdout.channel.recv_exit_status() != 0:
                print("stdout exit status: %s" %
                      stdout.channel.recv_exit_status())
                data_err = stderr.channel.recv_stderr(1024)
                if data_err:
                    print(data_err)
                exit(1)
        else:
            print("Error no command requested")
            exit(1)

    def source(self):
        self.exec_ssh(command=self.sudo_command + "source /root/openrc")

    def stop_all_swif_servers(self):
        self.exec_ssh(command=self.sudo_command + " swift-init all stop")

    def erase_swift_data(self):
        self.exec_ssh(command=self.sudo_command + " swift delete --all")

    def close(self):
        if self.ssh:
            self.ssh.close()

class FilePathWrapper():
    file_name = ""
    file_path = ""

    def __init__(self, file_name, file_path):
        self.file_name = file_name
        self.file_path = file_path


class COSBenchWorkload():
    cli_path = ""
    workload_path = ""
    filepaths = []
    storage_policies = []
    executions_count = 0
    proxy_node_ssh = None

    def __init__(self, cli_path, workload_path, ,
                 executions_count, proxy_node_ssh):
        self.cli_path = cli_path
        self.workload_path = workload_path
        self.sort_strategies = sort_strategies
        self.executions_count = executions_count
        self.proxy_node_ssh = proxy_node_ssh

    def _get_workloads(self):
        filepaths = []
        for f in sorted(listdir(self.workload_path)):
            if "xml" in f:
                file_path_wrapper = FilePathWrapper(f, self.workload_path + f)
                filepaths.append(file_path_wrapper)
        self.filepaths = filepaths

    def _restart_cosbench(self):
        cur_dir = os.getcwd()
        os.chdir(self.cli_path)
        ret = subprocess.call(["./stop-all.sh"])
        print("return: %s" % ret)
        ret = subprocess.call(["./start-all.sh"])
        print("return: %s" % ret)
        os.chdir(cur_dir)

    def _update_workload_xml(self,
                             current_file_path,
                             current_strategy):
        tree = ET.parse(current_file_path.file_path)
        root = tree.getroot()
        root.set('name', current_file_path.file_name + "-" +
                 current_strategy.strip())
        tree.write(current_file_path.file_path)










if __name__ == "__main__":
    parser = SafeConfigParser()
    parser.read("conf/cosbench_experiment.conf")