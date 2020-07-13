#!/usr/bin/python3
"""
This is a script to make iso of openeuler
"""

import os
import re
import sys
import subprocess
import argparse
import configparser
import shutil
import datetime

from common_var_func import CommonVars, CommonFunc
from down_rpm import download_rpms, get_rpm_pub_key
from create_iso import CreateIso

def mk_clean(tmp_build_dir):
    try:
        tmp_build_dir
    except NameError:
        print("No BUILD dir to be clean")
    else:
        shutil.rmtree(tmp_build_dir)
        shutil.rmtree("/etc/yum.repos.d")
        os.rename("/etc/repos.old", "/etc/yum.repos.d")

def create_install_img(common_vars):
    repos = " " + common_vars.REPOS1
    repos_s = repos.replace(" ", " -s ")
    cmd = "lorax " + "--isfinal " +  "-p " + common_vars.NAME + " -v " + common_vars.VERSION + " -r " + common_vars.RELEASE \
            + " --sharedir " + "80-openeuler " + "--rootfs-size " + "3 " + "--buildarch " + para.ARCH + \
            repos_s +  " --nomacboot " + "--noupgrade " + common_vars.BUILD + "/iso"
    lorax_logfile = "lorax.logfile"
    with open(lorax_logfile, "w") as lorax_log:
        res = subprocess.Popen(cmd, shell=True, stdout = lorax_log, stderr = lorax_log)
    return res

def create_repos(common_vars):
    # if /etc/repos.old is already exist, back up to a new dir depends on time
    if os.path.isdir("/etc/repos.old"):
        TIMEFORMAT = '%Y-%m-%d-%H:%M:%S'
        thetime = datetime.datetime.now().strftime(TIMEFORMAT)
        new_old_repo = "repos.old-" + thetime
        os.rename("/etc/repos.old/", new_old_repo)

    os.rename("/etc/yum.repos.d", "/etc/repos.old")
    os.mkdir("/etc/yum.repos.d/")
    repos = re.split(r'[\s]', common_vars.REPOS1)
    for repo in repos:
        res = subprocess.call(["yum-config-manager", "--add-repo", repo])
        if res != 0:
            raise RuntimeError("create repo failed!",res)
    subprocess.call("yum clean all",shell = True)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--config_file", type=str, help="Config file")
    parser.add_argument("-n", "--name", type=str, help="Name for iso")
    parser.add_argument("-v", "--version", type=str, help="Version for iso")
    parser.add_argument("-s", "--release", type=str, help="Release for iso")
    parser.add_argument("-r", "--repos", type=str, help="Repos used for building iso")
    parser.add_argument("-a", "--arch", type=str, help="Arch for iso")
    parser.add_argument("-d", "--dbg_flag", help="Enable debug iso", action="store_true")
    args = parser.parse_args()

    variables = CommonVars(args)
    
    print("-----env init start-----")
    variables.env_init()
    print("-----env init finish-----")

    print("-----create lorax install image start-----")
    create_img = create_install_img(variables)

    print("-----create repos-----")
    create_repos(variables)
    print("-----create repos-----")

    print("-----download packages-----")
    download_rpms(variables)
    print("-----download packages-----")

    print("-----wait lorax to finish, please wait-----")
    create_img_res = create_img.wait()
    print("-----create lorax install image finish-----")

    if create_img_res == 0:
        CommonFunc().print_file("lorax.logfile")
    else:
        CommonFunc().print_file("lorax.logfile")
        err = "create install image through lorax failed, see lorax.logfile for more detail!"
        raise RuntimeError(err, create_img_res)

    variables.cfg_init()

    get_rpm_pub_key(variables.BUILD)

    if variables.DBG_FALG == 1:
        # to be done
    else:
        CreateIso().gen_iso(variables)

    mk_clean(variables.BUILD)
