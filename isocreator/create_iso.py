#!/usr/bin/python3

import os
import subprocess

from common_var_func import CommonFunc

class CreateIso(object):
    def gen_iso(self, common_vars):
        release_name = common_vars.RELEASE_NAME
        iso_name = os.path.join("/result/", common_vars.ISO_NAME)
        iso_dir = os.path.join(common_vars.BUILD, "iso/")
        gen_iso_log = open("gen_iso_log.txt", "w")
        if common_vars.ARCH == "x86_64":
            cmd = "mkisofs -R -J -T -r -l -d -joliet-long -allow-multidot -allow-leading-dots "\
                    "-no-bak -V release_name -o " + iso_name + " -b isolinux/isolinux.bin -c "\
                    "isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot "\
                    "-e images/efiboot.img -no-emul-boot " + iso_dir
            res = subprocess.run(cmd, shell = True, stdout = gen_iso_log, stderr = gen_iso_log)
            gen_iso_log.close()
            if res.returncode != 0:
                CommonFunc().print_file("gen_iso_log.txt")
                raise RuntimeError("Make iso of X86_64 failed!",res)
        elif common_vars.ARCH == "aarch64":
            cmd = "mkisofs -R -J -T -r -l -d -joliet-long -allow-multidot -allow-leading-dots "\
                    "-no-bak -V " + release_name + " -o " + iso_name + " -e images/efiboot.img "\
                    "-no-emul-boot" + iso_dir
            res = subprocess.run(cmd, shell = True, stdout = gen_iso_log, stderr = gen_iso_log)
            gen_iso_log.close()
            if res.returncode != 0:
                CommonFunc().print_file("gen_iso_log.txt")
                raise RuntimeError("Make iso of aarch64 failed!",res)
        print(iso_name)
        cmd = "implantisomd5 " + iso_name
        res = subprocess.run(cmd, shell = True)
        print(res)
