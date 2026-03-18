#coding: utf-8

from __future__ import unicode_literals

import os
import tempfile
import click
import struct
import six
import zipfile
import uuid
import shutil

if six.PY2:
    from urllib import urlretrieve
else:
    from urllib.request import urlretrieve



TRADE_DLL_KEY = "http://alpha-evolver1982.coding.me/tts/Trade.dll"
ALFE_TRADE_SEVER_KEY = "http://alpha-evolver1982.coding.me/tts/AlfeTradeServer-Release-1.8_20180326103850.zip"



def main():

    # 1 give me a tmp dir

    base_dir = tempfile.gettempdir()
    dll_path = os.path.join(base_dir, "dll")
    download_path = os.path.join(base_dir, "download")
    try:
        if not os.path.isdir(dll_path):
            os.makedirs(dll_path)
    finally:
        pass

    try:
        if not os.path.isdir(download_path):
            os.makedirs(download_path)
    finally:
        pass

    # 2 Confirm installation

    to_say = """
Hello, running this command will start the AlfeTradeServer installation process.
The installer will install AlfeTradeServer and configure its dependency trade.dll.

Note: trade.dll is from the internet, AlfeTradeServer only provides simple wrapper for trade.dll,
making it available for REST API, and provides alfe calls.
This program has not done any research on TDX transmission protocol, all trade.dll and its binding method are from the internet.

[rest       ]   AlfeTradeServer : https://github.com/alpha-evolver/AlfeTradeServer
[client api ]   alfe : https://github.com/alpha-evolver/alfe

Do you want to continue? Will download the corresponding trade.dll and configure it.

Created by alpha-evolver with love!

    """
    click.secho(to_say, fg='green')

    yes_to_continue()

    se("Starting to download trade.dll...")
    trade_dll_template = os.path.join(dll_path, "trade.dll")
    urlretrieve(TRADE_DLL_KEY, trade_dll_template)
    se("Download complete....")

    se("To use trade.dll, you need to bind an account")
    acc = click.prompt("Please enter your account")
    se("Your account is {}".format(acc), fg="green")
    sig = make_sig(acc)
    se("Generating usable trade.dll binding: sig is [{}]".format(sig))
    with open(trade_dll_template, 'rb') as f:
        content = f.read()

    real_trade_dll_name = "trade_alfe_{}.dll".format(acc)
    real_trade_dll_path = os.path.join(dll_path, real_trade_dll_name)
    lenof_sig = len(sig)

    with open(real_trade_dll_path, "wb") as f:
        start_offset = 1132713
        f.write(content[:start_offset])
        f.write(sig)
        f.write(content[start_offset + lenof_sig:])
    se("Write complete, file name: {}".format(real_trade_dll_path))

    se("Starting to download AlfeTradeServer....")
    download_and_setup_alfe_trade_server(download_path, dll_path, real_trade_dll_name)


def download_and_setup_alfe_trade_server(download_path, dll_path, real_trade_dll_name):
    zip_file_path = os.path.join(download_path, "tts.zip")
    urlretrieve(ALFE_TRADE_SEVER_KEY, zip_file_path)
    print(download_path)

    if os.path.isfile(zip_file_path):
        se("Download complete")
    else:
        raise SystemExit("Download failed")

    se("Starting to extract")
    zf = zipfile.ZipFile(file=zip_file_path)
    zf.extractall(dll_path)
    zf.close()
    se("Extraction complete")

    config_file_content, bind_ip, bind_port, enc_key, enc_iv = gen_config_file(real_trade_dll_name)

    config_file_name = "AlfeTradeServer.ini"
    with open(os.path.join(dll_path, config_file_name), "w") as f:
        f.write(config_file_content)
    se("Config file written, file name AlfeTradeServer.ini")
    while True:
        _dir = click.prompt("Please select program installation path", "C:\\AlfeTradeServer")
        if os.path.exists(_dir):
            click.secho("Directory already exists, please select a new path")
        else:
            break

    os.makedirs(_dir)
    os.rmdir(_dir)
    shutil.copytree(dll_path, _dir)
    se("Copy complete! Please run AlfeTradeServer.exe in path {} to start the service".format(_dir), fg="green")

    se("For client, you can use alfe's trade module to connect, below is a demo code showing how to initialize the object")

    demo_code = """
import os
from alfe.trade import AlfeTradeApi
api = AlfeTradeApi(endpoint="http://{}:{}/api", enc_key=b"{}", enc_iv=b"{}")
print("---Ping---")
result = api.ping()
print(result)

print("---Login---")
acc = os.getenv("ALFE_ACCOUNT", "") ###### Your account
password = os.getenv("ALFE_PASS", "") ###### Your password
result = api.logon("<ip addr>", 7708,
          "8.23", 32,
          acc, acc, password, "")

print(result)

if result["success"]:
    client_id = result["data"]["client_id"]

    for i in (0,1,2,3,4,5,6,7,8,12,13,14,15):
        print("---Query info cate=%d--" % i)
        print(api.data_to_df(api.query_data(client_id, i)))


    print("---Query quotes---")
    print(api.data_to_df(api.get_quote(client_id, '600315')))

    print("---Logout---")
    print(api.logoff(client_id))
    """.format(bind_ip, bind_port, enc_key, enc_iv)

    demo_sample = """
from alfe.trade import AlfeTradeApi
api = AlfeTradeApi(endpoint="http://{}:{}/api", enc_key=b"{}", enc_iv=b"{}")
    """.format(bind_ip, bind_port, enc_key, enc_iv)

    print("-"*30)
    print(demo_sample)
    print("-"*30)

    demo_path = os.path.join(_dir, "demo.py")
    with open(demo_path, "w") as f:
        f.write(demo_code)
    se("alfe demo code is at {}".format(demo_path),fg="blue")
    se("Note: v1.5+ supports multi-account version, for how to configure multi-account version, see https://github.com/alpha-evolver/AlfeTradeServer", fg="red")
    se("Happy Trading!", fg="green")


def gen_config_file(real_trade_dll_name):
    se("Starting to generate config file..")
    random_uuid = uuid.uuid1().hex
    enc_key = random_uuid[:16]
    enc_iv = random_uuid[16:]
    se("Generated enc_key = [{}] , enc_iv = [{}]".format(enc_key, enc_iv))
    bind_ip = click.prompt('Please enter bind IP address', default="127.0.0.1")
    bind_port = click.prompt('Please enter bind port', default="19820")
    config_file_content = """bind={}
port={}
trade_dll_path={}
transport_enc_key={}
transport_enc_iv={}
""".format(bind_ip, bind_port, real_trade_dll_name, enc_key, enc_iv)

    return config_file_content, bind_ip, bind_port, enc_key, enc_iv



def yes_to_continue():
    while True:
        c = click.prompt('Do you want to continue? Enter y to continue, n to exit? ', default="y")
        if c.lower() == 'n':
            click.secho("You chose to exit")
            raise SystemExit("need to exit")
        elif c.lower() == "y" or c == "":
            return

def make_sig(acc):

    if type(acc) is six.text_type:
        acc = acc.encode("utf-8")

    a3 = 0x55e
    # Odd positions
    gpdm = acc[::2]
    # print("Odd positions: {}".format(gpdm))

    result = b""
    for c in gpdm:

        if six.PY2:
            (c,) = struct.unpack("b", c)

        _next = True
        a = c
        b = a3 >> 0x8
        c = a ^ b
        a3 = (0x207f * (a3 + c) - 0x523d) & 0xffff
        j = 64
        while _next:
            j += 1
            if j > 90:
                break
            k = 91
            while _next:
                k -= 1
                if k < 65:
                    break

                temp = 1755 + c - k
                if temp % 26 == 0 and temp // 26 == j:

                    result += struct.pack("bb", j, k)
                    _next = False
    return result


def se(*args, **kwargs):
    _args = list(args)
    _args[0] = "[    alfe   ] " + _args[0]
    click.secho(*_args, **kwargs)

if __name__ == '__main__':
    try:
        main()
        # gen_config_file()
    except SystemExit:
        exit()
