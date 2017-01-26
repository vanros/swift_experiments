import sys
from subprocess import Popen, PIPE
import subprocess
from os import listdir
import os
from ConfigParser import SafeConfigParser
import time
import shutil
import xml.etree.ElementTree as ET
import select
from fabric.api import env, run
from fabric.api import task
from fabric.tasks import Task
from fabric.network import disconnect_all

#SWIFT_CONF_DIR = "swift_conf"

class SwiftNodeSSH():
    ip = []
    def __init__(self, ip):
        self.ip = ip

    for i in ip:
        currenty_ip = ip[i]
        env.hosts.append(currenty_ip)

    def source(self):
        run("source /root/openrc")

    def stop_all_swif_servers(self):
        run(" swift-init all stop")

    def erase_swift_data(self):
        run(" swift delete --all")

    #função para criar rings
    def create_rings(self, id_ring, partitions_count, replicas_count, ip_port, disk):
                run("cd etc/swift directory")
                run("swift-ring-builder object-"+id_ring+".builder create"+ partitions_count + replicas_count + "1")
                run("swift-ring-builder object-"+id_ring+".builder add r1z"+disk+"-"+ip_port+"/"+disk+ "1")
                run("swift-ring-builder object-"+id_ring+".builder rebalance")

    def restart_swift(self):
        run("swift-init all restart")

    def close_SSH(self):
        disconnect_all()



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
        SwiftNode = SwiftNodeSSH()
        for filepath in self.filepaths:
            for current in range(self.executions_count):
                print("filepath: %s" % filepath.file_path)
                for storage_policy in self.storage_policies:
                    SwiftNode.source()
                    SwiftNode.stop_all_swif_servers()
                    SwiftNode.erase_swift_data()
                    policy_values = storage_policy.split(" ")
                    for policy_value in policy_values:
                        conf_values = policy_value.split("/")
                        id_ring = conf_values[0]
                        partitions_count = conf_values[1]
                        replicas_count = conf_values[2]
                        ip_port = conf_values[3]
                        disk = conf_values[4]
                        SwiftNode.create_rings(id_ring,partitions_count,replicas_count,ip_port,disk)

                SwiftNode.restart_swift()
                time.sleep(1)
                self._update_workload_xml()


if __name__ == "__main__":
    parser = SafeConfigParser()
    parser.read("conf/cosbench_experiment.conf")

    workload_path = os.path.join(parser.get("cosbench_experiment",
                                            "workload_path"), '')

    cli_path = os.path.join(parser.get("cosbench", "root_path"), '')

    swift_proxy_node_ip_list = list(parser.get("swift_proxy_node",
                                                   "ip_list").split('\n'))
    swift_proxy_node_ip_list = swift_proxy_node_ip_list[1:]

    execution_01_storage_policies = list(parser.get("execution_01",
                                                   "storage_policies").split('\n'))
    execution_01_storage_policies = execution_01_storage_policies[1:]

    execution_01_executions_count = int(parser.get("execution_01",
                                                   "executions_count"))

    print(cli_path)
    print(workload_path)
    print(swift_proxy_node_ip_list)
    print(execution_01_storage_policies)
    print(execution_01_executions_count)

    swift_node_ssh = SwiftNodeSSH(swift_proxy_node_ip_list)

    execution_01 = COSBenchWorkload(cli_path,
                                    workload_path,
                                    execution_01_storage_policies,
                                    execution_01_executions_count,
                                    swift_node_ssh)
    execution_01.run()


    swift_node_ssh.close_SSH()



