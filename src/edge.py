import logging
from typing import Optional

import paramiko
from scp import SCPClient


class EdgeConnection(object):
    def __init__(self, address: str, username: str, certificate_path: str, port: int = 22):
        self.address = address
        self.username = username
        self.certificate = certificate_path
        self.port = port
        self.ssh_client = None
        self.ssh_client = self.connect()

    def connect(self) -> Optional[paramiko.SSHClient]:
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                hostname=self.address,
                port=self.port,
                username=self.username,
                key_filename=self.certificate,
                timeout=20,
                look_for_keys=False,
            )
            logging.info(f"Connected to {self.address} over SSH")

        except Exception as e:
            ssh_client = None
            logging.error(f"Unable to connect to {self.address} over SSH: {e}")
        return ssh_client

    def send_command(self, command: str) -> None:
        if self.ssh_client:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            while not stdout.channel.exit_status_ready():
                # Print data when available
                if stdout.channel.recv_ready():
                    alldata = stdout.channel.recv(1024)
                    prevdata = b"1"
                    while prevdata:
                        prevdata = stdout.channel.recv(1024)
                        alldata += prevdata
                    logging.info(str(alldata))
        else:
            logging.error(f"Connection to Edge server {self.address} not opened.")

    def upload_folder(self, source_folder: str, target_folder: str) -> None:
        if self.ssh_client:
            scp = SCPClient(self.ssh_client.get_transport())
            scp.put(files=source_folder, remote_path=target_folder, recursive=True)

    def upload_edge_shared_folder(self, edge_directory: str, shared_connection_folder: str) -> None:
        self.send_command(
            command=f"sudo ./edgecli objects folder-upload --source {edge_directory} \
            --target {shared_connection_folder}"
        )
