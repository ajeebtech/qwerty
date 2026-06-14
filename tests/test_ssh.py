import pytest
from unittest.mock import MagicMock, patch, call

import cli.ssh as ssh
from cli.ssh import SSHManager, is_destructive

def test_is_destructive():
    # Destructive commands
    assert is_destructive("rm -rf /") is True
    assert is_destructive("rm -rf *") is True
    assert is_destructive("rm somefile.txt") is True
    assert is_destructive("mkfs.ext4 /dev/sdb") is True
    assert is_destructive("dd if=/dev/zero of=/dev/sda") is True
    assert is_destructive("shutdown -h now") is True
    assert is_destructive("reboot") is True
    assert is_destructive("systemctl stop nginx") is True
    assert is_destructive("init 6") is True
    
    # Safe commands
    assert is_destructive("ls -la") is False
    assert is_destructive("df -h") is False
    assert is_destructive("echo 'rm -rf'") is False
    assert is_destructive("cat file.txt") is False

@patch("cli.ssh.paramiko.SSHClient")
def test_ssh_connect(mock_client_cls):
    mock_client = mock_client_cls.return_value
    
    manager = SSHManager(host="1.2.3.4", user="ubuntu", port=22, password="password")
    assert manager.connect() is True
    mock_client.connect.assert_called_once_with(
        hostname="1.2.3.4",
        port=22,
        username="ubuntu",
        timeout=15,
        look_for_keys=True,
        allow_agent=True,
        password="password"
    )

@patch("cli.ssh.paramiko.SSHClient")
@patch("cli.display.status_command")
def test_ssh_run_stream(mock_status, mock_client_cls):
    mock_client = mock_client_cls.return_value
    mock_channel = MagicMock()
    
    # Setup channel mocks to return chunks
    mock_channel.exit_status_ready.side_effect = [False, False, True]
    mock_channel.recv_ready.side_effect = [True, True, True, False]
    mock_channel.recv.side_effect = [b"hello", b" world", b""]
    mock_channel.recv_exit_status.return_value = 0
    
    # exec_command returns stdin, stdout, stderr
    mock_stdout = MagicMock()
    mock_stdout.channel = mock_channel
    
    mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())
    
    manager = SSHManager(host="1.2.3.4", user="ubuntu")
    manager.client = mock_client
    
    output, code, duration = manager.run("echo 'hello world'", was_dry_run=False)
    
    assert output == "hello world"
    assert code == 0
    assert duration >= 0
    mock_client.exec_command.assert_called_once_with("echo 'hello world'", get_pty=True)

@patch("cli.display.status_dry_run")
def test_ssh_run_dry_run(mock_dry_run):
    manager = SSHManager(host="1.2.3.4", user="ubuntu")
    output, code, duration = manager.run("rm -rf /", was_dry_run=True)
    assert output == ""
    assert code == 0
    mock_dry_run.assert_called_once_with("rm -rf /")

@patch("cli.display.status_destructive_prompt", return_value=False)
def test_ssh_destructive_command_rejected(mock_prompt):
    manager = SSHManager(host="1.2.3.4", user="ubuntu")
    output, code, duration = manager.run("rm -rf /", was_dry_run=False)
    assert code == -1
    assert "cancelled" in output
    mock_prompt.assert_called_once()

@patch("cli.ssh.paramiko.SSHClient")
@patch("sys.stdout.write")
def test_ssh_run_custom_color(mock_stdout_write, mock_client_cls):
    mock_client = mock_client_cls.return_value
    mock_channel = MagicMock()
    mock_channel.exit_status_ready.side_effect = [True]
    mock_channel.recv_ready.return_value = False
    mock_channel.recv_exit_status.return_value = 0
    mock_stdout = MagicMock()
    mock_stdout.channel = mock_channel
    mock_client.exec_command.return_value = (MagicMock(), mock_stdout, MagicMock())
    
    manager = SSHManager(host="1.2.3.4", user="ubuntu", log_color="cyan")
    manager.client = mock_client
    
    manager.run("echo 'test'", was_dry_run=False)
    mock_stdout_write.assert_any_call("\033[36m")
