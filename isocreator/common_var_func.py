#!/usr/bin/python3

import os
import re
import sys
import subprocess
import configparser
import shutil

class CommonVars(object):
    CONFIG_FILE = NAME = VERSION = RELEASE = REPOS1 = ARCH = ""
    CONFIG = RELEASE_NAME = ISO_NAME = SRC_ISO_NAME = DBG_ISO_NAME = ""
    TYPE, BUILD, SRC_DIR, DBG_DIR = "iso", "/result/tmp/", "/result/tmp/src/", "/result/tmp/dbg/"
    DBG_FLAG = 0
    config_dict = {}

    def __init__(self, args):
        if args.config_file:
            self.CONFIG_FILE = args.config_file
        if args.name:
            self.NAME = args.name
        if args.version:
            self.VERSION = args.version
        if args.release:
            self.RELEASE = args.release
        if args.repos:
            self.REPOS1 = args.repos
        if args.arch:
            self.ARCH = args.arch
        if args.dbg_flag:
            self.DBG_FLAG = 1

        self.RELEASE_NAME = self.NAME + "-" + self.VERSION + "-" + self.ARCH
        self.ISO_NAME = self.NAME + "-" + self.VERSION + "-" + self.ARCH + "-dvd.iso"
        self.SRC_ISO_NAME = self.NAME + "-" + self.VERSION + "-" + "-source-dvd.iso"
        self.DBG_ISO_NAME = self.NAME + "-" + self.VERSION + "-" + "-debug-dvd.iso"

        if self.CONFIG_FILE and os.path.isfile(self.CONFIG_FILE):
            with open(self.CONFIG_FILE) as config_file:
                for line in config_file:
                    line = line.strip("\n")
                    config_key = re.sub(r"=.*", "", line)
                    config_value = re.sub(r".*=\"", "", line)
                    config_value = config_value.strip("\"")
                    # if the config_value is empty, do not put it
                    # into dict
                    if config_value:
                        self.config_dict[config_key] = config_value
                    else:
                        continue

    def env_init(self):
        if os.path.isdir(self.BUILD):
            iso_path = os.path.join(self.BUILD, "iso")
            if os.path.isdir(iso_path):
                shutil.rmtree(iso_path)
        else:
            os.makedirs(self.BUILD)

        res = subprocess.call("setenforce 0", shell = True)
        if res != 0:
            raise RuntimeError("setenforce failed!",res)

    def cfg_init(self):
        sdf_file = os.path.join(self.BUILD, "isopackage.sdf")
        if os.path.isfile(sdf_file):
            shutil.copy(sdf_file, os.path.join(self.BUILD, "iso"))

        ks_file_key = "CONFIG_KS_FILE"
        ks_file_value = self.config_dict.get(ks_file_key)
        if ks_file_value:
            ks_dir = os.path.join(self.BUILD, "iso/ks/")
            os.makedirs(ks_dir)
            shutil.copy(ks_file_value, ks_dir)
        else:
            print("No CONFIG_KS_FILE")

        """
        # Copy OpenEuler Software License
        # temporary we don't do this, to be done
        license_file = os.path.join(self.BUILD, "docs/OpenEuler-Software-License.docx")
        if not os.path.isfile(license_file):
            docs_dir = os.path.join(self.BUILD, "iso/docs")
            iso_dir = os.path.join(self.BUILD, "iso")
            # if docs_dir exists as file or dir, copytree dir docs
            # to docs_dir will fail
            if os.path.exists(docs_dir):
                shutil.rmtree(docs_dir)
            if os.path.isdir(iso_dir):
                pass
            else:
                os.makedirs(iso_dir)
            shutil.copytree("/opt/mkeuleros/docs/", docs_dir)
        """

class CommonFunc(object):
    # print the content of file to screen
    def print_file(self, file_to_print):
        with open(file_to_print, "r") as fr:
            for line in fr:
                line = line.strip("\n")
                print(line)

    # search specific string in text file
    def search_str(self, file_to_find, str_to_find):
        with open(file_to_find, "r") as fr:
            for line in fr.readlines():
                if str_to_find in line:
                    return True
        return False

if __name__ == "__main__":
    pass
