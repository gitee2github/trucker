#!/usr/bin/python3
"""
public api
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
import shlex
import shutil
import subprocess


class PubApi(object):
    """
    public api
    """
    def Read_Write(self, src, dst):
        """
        read a file and append to another one
        :param src:
        :param dst:
        :return:
        """
        srcfile = open(src)
        for line in srcfile:
            with open(dst, "a") as dstfile:
                dstfile.write(line)
        dstfile.close()
        srcfile.close()
        if os.path.exists(dst) == True:
            return True
        else:
            return False

    def run_cmd(self, cmd):
        """
        run command
        :param cmd:
        :return:
        """
        cmd = shlex.split(cmd)
        res = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sout = res.communicate()
        return res.returncode, sout[0].decode()

    def copy_file(self, srcpath, dstpath):
        """
        copy file from srcpath to dstpath
        :param srcpath:
        :param dstpath:
        :return:
        """
        if not os.path.exists(srcpath):
            print("srcpath not exist!")
        if not os.path.exists(dstpath):
            print("dstpath not exist")
        for root, dirs, files in os.walk(srcpath, True):
            for eachfile in files:
                shutil.copy(os.path.join(root, eachfile), dstpath)

    def mkdir(self, path):
        """
        make dir
        :param path:
        :return:
        """
        path = path.strip()
        Exist = os.path.exists(path)
        if not Exist:
            os.makedirs(path.decode('utf-8'))
            print(path + 'dir is maked success')
            return True
        else:
            print(path + 'dir is already exist,no need to make dir')
            return False

    def check_tools(self, tools):
        """
        check tools
        :param tools:
        :return:
        """
        flag = True
        for tool in tools:
            cmd = "which " + tool
            ret = self.run_cmd(cmd)
            if ret[0] != 0:
                flag = False
                print("Need tool %s" % tool)
                print("Lack necessary tool!!!")
                return 2
        return 0
