#!/usr/bin/python3

import os
import subprocess
import shutil

from common_var_func import CommonFunc

class CreateIso(object):
    def make_iso(self, arch, release_name, iso_full_name, iso_dir):
        gen_iso_log = open("gen_iso_log.txt", "w")
        if arch == "x86_64":
            cmd = "mkisofs -R -J -T -r -l -d -joliet-long -allow-multidot -allow-leading-dots "\
                    "-no-bak -V " + release_name + " -o " + iso_full_name + " -b isolinux/isolinux.bin -c "\
                    "isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot "\
                    "-e images/efiboot.img -no-emul-boot " + iso_dir
            res = subprocess.run(cmd, shell = True, stdout = gen_iso_log, stderr = gen_iso_log)
        elif arch == "aarch64":
            cmd = "mkisofs -R -J -T -r -l -d -joliet-long -allow-multidot -allow-leading-dots "\
                    "-no-bak -V " + release_name + " -o " + iso_full_name + " -e images/efiboot.img "\
                    "-no-emul-boot " + iso_dir
            res = subprocess.run(cmd, shell = True, stdout = gen_iso_log, stderr = gen_iso_log)
        gen_iso_log.close()
        if res.returncode != 0:
            CommonFunc().print_file("gen_iso_log.txt")
            raise RuntimeError("Make iso of %s failed!"% arch,res)
        cmd = "implantisomd5 " + iso_full_name
        res = subprocess.run(cmd, shell = True)
        print(res)

    def gen_install_iso(self, common_vars):
        iso_full_name = os.path.join("/result/", common_vars.ISO_NAME)
        iso_dir = os.path.join(common_vars.BUILD, "iso/")
        self.make_iso(common_vars.ARCH, common_vars.RELEASE_NAME, iso_full_name, iso_dir)

    def gen_dbg_iso(self, common_vars):
        # delete the repodata files
        repo_dir = os.path.join(common_vars.BUILD, "iso/repodata/")
        pkgs_dir = os.path.join(common_vars.BUILD, "iso/Packages/")
        iso_dir = os.path.join(common_vars.BUILD, "iso")
        iso_full_name = os.path.join("/result/", common_vars.DBG_ISO_NAME)
        CommonFunc().delete_files_in_dir(repo_dir, "*")
        shutil.copy(common_vars.config_dict.get("CONFIG_PACKAGES_LIST_FILE"), repo_dir)
        CommonFunc().delete_file_dir(pkgs_dir)
        shutil.move(common_vars.DBG_DIR, pkgs_dir)
        cmd = "createrepo -g " + repo_dir + "*.xml" + " " + iso_dir
        subprocess.run(cmd, shell = True)
        self.make_iso(common_vars.ARCH, common_vars.RELEASE_NAME, iso_full_name, iso_dir)

    def gen_src_iso(sel, common_vars):
        pkgs_dir = os.path.join(common_vars.BUILD, "iso/Packages")
        iso_dir = os.path.join(common_vars.BUILD, "iso")
        iso_full_name = os.path.join("/result/", common_vars.SRC_ISO_NAME)
        delete_file_dir(pkgs_dir)
        shutil.move(common_vars.SRC_DIR, pkgs_dir)
        self.make_iso(common_vars.ARCH, common_vars.RELEASE_NAME, iso_full_name, iso_dir)
