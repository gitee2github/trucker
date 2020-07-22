#!/usr/bin/python3
"""
Tool to make livecd
"""
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: Shinwell_Hu Myeuler
# Create: 2020-05-07
# Description: provide a tool to package python module automatically
# ******************************************************************************/

import os
import shutil
import subprocess
import sys
import configparser
import pubapi

Need_Tools = (
    'yum',
    'setenforce',
    'rpm',
    'mkdir',
    'livemedia-creator')
mypubapi = pubapi.PubApi()
conf = configparser.ConfigParser()


class LiveConf(object):
    """
    config info
    """

    def __init__(self):
        self.ISO_NAME = conf["DEFAULT"]["ISO_NAME"]
        self.ISO_VERSION = conf["DEFAULT"]["ISO_VERSION"]
        self.ARCH = os.uname()
        self.DVD_NAME = self.ISO_NAME + self.ISO_VERSION + self.ARCH + '-dvd.iso'
        self.repo = conf["DEFAULT"]["repo"]
        self.BUILD_SCRIPT_DIR = os.getcwd()
        self.loraxdir = conf["DEFAULT"]["loraxdir"]
        self.ks = os.getcwd() + conf["DEFAULT"]["ksdir"] + self.ARCH + ".ks"
        self.ISCHROOT = 0
        self.OBSIP = conf["DEFAULT"]["OBSIP"]
        self.OBSURL = conf["DEFAULT"]["OBSURL"]
        self.OBSNAME = conf["DEFAULT"]["OBSNAME"]

    def check_env(self):
        """
        function: config obs in /etc/hosts
        :return:
        """
        if self.ISCHROOT == 0:
            mypubapi.run_cmd('echo {0} {1} >>/etc/hosts'.format(self.OBSNAME, self.OBSIP))

    def getinfo(self):
        """
        placeholder
        :return:
        """


Live_Conf = LiveConf()


def make_livecd(islocal, yum_repo):
    """
    function:make livecd
    :return:
    """
    yum_path = '/etc/yum.repos.d'
    shutil.rmtree(path=yum_path)
    mypubapi.mkdir(yum_path)
    if islocal != 0:
        Live_Conf.check_env()
        # obsconf obs repo
        obsconf = "config/repo_conf/obs-{0}.conf".format(Live_Conf.ARCH)
        ret = pubapi.Read_Write(obsconf, Live_Conf.repo)
        if ret != True:
            print("obsconf is not writed to yum_repo")
    else:
        # local repo from iso mounted
        if yum_repo != '':
            f = open(yum_path + '/local.repo', 'w')
            f.write('''[OS-base]
                    name=OS-base
                    baseurl={0}
                    enable=1
                    gpgcheck=0
            '''.format(yum_repo))
            f.close()
    mypubapi.run_cmd("yum clean all")
    subprocess.call("yum install -y lorax anaconda libselinux-utils", shell=True)
    mypubapi.run_cmd('setenforce 0')
    sed_cmd = "s/PRODUCT_NAME/{0}-{1}/ {2}/config/livecd/euleros-livecd{3},ks".format(Live_Conf.ISO_NAME,
                                                                                      Live_Conf.IS0_VERSION,
                                                                                      Live_Conf.BUILD_SCRIPT_DIR,
                                                                                      Live_Conf.ARCH)
    mypubapi.run_cmd(sed_cmd)
    Exist = os.path.exists("{0}live".format(Live_Conf.loraxdir))
    if Exist:
        ret = shutil.rmtree("{0}live".format(Live_Conf.loraxdir))
        shutil.copytree('config/livecd/live', "{0}live".format(Live_Conf.loraxdir))
    else:
        print("start copyfile")
        shutil.copytree('config/livecd/live', "{0}live".format(Live_Conf.loraxdir))
    mypubapi.mkdir('/tmp')
    ret = mypubapi.run_cmd('livemedia-creator --make-iso \
                          --ks={0} --nomacboot --no-virt --project {1} --releasever {2} --tmp {3}/tmp \
                          --anaconda-arg="--nosave=all_ks" --dracut-arg="--xz" \
                          --dracut-arg="--add livenet dmsquash-live convertfs pollcdrom qemu qemu-net" \
                          --dracut-arg="--omit" --dracut-arg="plymouth"  --dracut-arg="--no-hostonly" \
                          --dracut-arg="--debug" --dracut-arg="--no-early-microcode" \
                          --dracut-arg="--nostrip"'.format(Live_Conf.ks, Live_Conf.ISO_NAME, Live_Conf.IS0_VERSION,
                                                           os.getcwd()))
    if ret[0] == 0:
        print("livecd is maked success")
    else:
        print("livecd is maked failed")
    return 0


if __name__ == "__main__":
    mypubapi.check_tools(Need_Tools)
    try:
        prog, arg_islocal, arg_yum_repo = sys.argv
        make_livecd(arg_islocal, arg_yum_repo)
    except Exception as e:
        print(e)
