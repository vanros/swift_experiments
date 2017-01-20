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
from fabric.api import env, run
from fabric.api import task
from fabric.tasks import Task

SWIFT_CONF_DIR = "swift_conf"

class SwiftNodeSSH(Task):
    ip = []
    def __init__(self, ip):
        self.ip = ip
    #env.hosts = ['192.168.1.100', '192.168.1.101', '192.168.1.102']
    for i in ip:
        currenty_ip = ip[i]
        env.hosts.append(currenty_ip)

    def source(self):
        run("source /root/openrc")

    def stop_all_swif_servers(self):
        run(" swift-init all stop")

    def erase_swift_data(self):
        run(" swift delete --all")



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

    def __init__(self, cli_path, workload_path, storage_policies,
                 executions_count, proxy_node_ssh):
        self.cli_path = cli_path
        self.workload_path = workload_path
        self.storage_policies = storage_policies
        self.executions_count = executions_count
        self.proxy_node_ssh = proxy_node_ssh

    def _get_workloads(self):
        filepaths = []
        for f in sorted(listdir(self.workload_path)):
            if "xml" in f:
                file_path_wrapper = FilePathWrapper(f, self.workload_path + f)
                filepaths.append(file_path_wrapper)
        self.filepaths = filepaths

    def _reset_archives(self):
        filename = raw_input('Delete old archives [y/n]: ')
        if "y" in filename:
            shutil.rmtree(self.cli_path + "archive", ignore_errors=True)
            self._restart_cosbench()

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
                             current_storage_policies):
        tree = ET.parse(current_file_path.file_path)
        root = tree.getroot()
        root.set('name', current_file_path.file_name + "-" +
                 current_storage_policies.strip())
        tree.write(current_file_path.file_path)

    def run(self):
        self._reset_archives()
        self._get_workloads()
        for filepath in self.filepaths:
            for current in range(self.executions_count):
                for storage_policy in self.storage_policies:
                    SwiftNodeSSH.source()













if __name__ == "__main__":
    parser = SafeConfigParser()
    parser.read("conf/cosbench_experiment.conf")