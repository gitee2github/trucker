#!/usr/bin/python3

import os
import re
import shutil
import glob
import subprocess
import xml.etree.ElementTree as ET

from common_var_func import CommonFunc as CF

# search sepcific package in specific file
def find_pkg(list_file, pkg_name):
    with open(list_file, "r") as fr:
        for line in fr:
            # the line starts with pkg
            #line = line.strip('\n')
            if line.startswith(pkg_name):
                return True
    return False

# down src rpm
def down_src_rpm(common_vars):
    if os.path.isdir(common_vars.SRC_DIR):
        shutil.rmtree(common_vars.SRC_DIR)
    os.makedirs(common_vars.SRC_DIR)
    src_pkgs_to_down = ""
    # list the rpm packages that already down to downed_pkgs.txt
    cmd = "ls " + os.path.join(common_vars.BUILD, "iso/Packages/")
    with open("downed_pkgs.txt", "w") as downed_pkgs:
        subprocess.run(cmd, shell = True, stdout = downed_pkgs)

    # get the src packages that need to be down
    with open("downed_pkgs.txt", "r") as downed_pkgs:
        lines_met = set()
        for line in downed_pkgs:
            line = line.strip("\n")
            if line not in lines_met:
                src_pkgs_to_down += re.sub(r".rpm\n$", " ", line)
                lines_met.add(line)
    
    cmd = "yumdownloader --install=" + os.path.join(common_vars.BUILD, "tmp") + " --source" \
            + " --destdir=" + common_vars.SRC_DIR
    subprocess.run(cmd, shell = True)
    cmd = "yumdownloader kernel-source --install="  + os.path.join(common_vars.BUILD, "tmp") + \
            " --destdir=" + common_vars.SRC_DIR
    return 0


# get rpm packages name for downloading
def get_down_pkg(yum_pkg_avail, rpm_list_uniq, specific_arch):
    not_found_flag = 0
    if os.path.isfile("down_list.txt"):
        os.remove("down_list.txt")

    with open(rpm_list_uniq, "r") as uniq_list:
        for line in uniq_list:
            line =line.strip('\n')
            rname = line
            rarch = re.sub(r'^.*\.','', line)
            # if the suffix of pkg is different from specific ARCH
            # change it
            if rarch == "i686" and specific_arch == "aarch64":
                continue
            if rarch == "x86_64" and specific_arch == "aarch64":
                rname = re.sub(r'\..*', '', line)
                rarch = "aarch64"
            if rarch == "aarch64" and specific_arch == "x86_64":
                rname = re.sub(r'\..*', '', line)
                rarch = "x86_64"

            if find_pkg(yum_pkg_avail, rname):
                all_archs = ["i686", "x86_64", "noarch", "aarch64"]
                if rarch not in all_archs:
                    rname_arch = rname + specific_arch
                    if find_pkg(yum_pkg_avail, rname_arch):
                        rname = rname_arch
                    else:
                        rname_noarch = rname + ".noarch"
                        if find_pkg(yum_pkg_avail, rname_noarch):
                            rname = rname_noarch
                        else:
                            with open("not_find.txt","a") as not_find:
                                not_find.write("cannot find %s in you repo\n" % (rname))
                            not_found_flag = 1
                            continue
                with open("down_list.txt", "a") as down_list:
                    rname += '\n'
                    down_list.write(rname)
            # if rname is not in available pacakge list
            else:
                with open("query_pkg.txt","w") as query_pkg:
                    query_res = subprocess.run(["repoquery", "--queryformat=%{name}.%{arch}",
                        "-q", "--whatprovides", rname], stdout = query_pkg)
                # file exist and not empty, the result of old version repoquery is listed as below:
                # repoquery --queryformat=%{name}.%{arch} -q --whatprovides xxx
                # ['--quereformat=%{name}.%{arch}', '-q', 'whatprovides', 'xxx']
                # <class 'list'>
                # ['repoquery', '--queryformat=%{name}.%{arch}', '-q', '--whatprovides', 'xxx']
                # so we need to judge the result of the query
                if os.path.getsize("query_pkg.txt"):
                    with open("query_pkg.txt", "r") as query_pkg:
                        lines = query_pkg.readlines()
                        last_line = lines[-1]
                        if last_line.startswith("['repoquery',"):
                            with open("not_find.txt", "a") as not_find:
                                not_find.write("can not find %s in your repo\n" % (rname))
                            not_found_flag = 1
                            os.remove("query_pkg.txt")
                            continue
                # file exist but empty
                else:
                    with open("not_find.txt", "a") as not_find:
                        not_find.write("can not find %s in your repo\n" % (rname))
                    not_found_flag = 1
                    os.remove("query_pkg.txt")
                    continue

    return not_found_flag

# download packages in xml
def download_rpms(common_vars):

    rpm_list = "rpm_list.txt"
    rpm_list_uniq = "rpm_list_uniq.txt"
    list_log = "list_pkg_log.txt"
    yum_pkg_avail = "yum_pkg_avail.txt"

    # get rpm packages from .xml
    rpm_file = ET.parse(common_vars.config_dict.get("CONFIG_PACKAGES_LIST_FILE"))
    pkg_list = rpm_file.findall("./group/packagelist")
    with open(rpm_list, "w") as pkgs_list_ori:
        for pkgs in pkg_list:
            for pkg in list(pkgs):
                pkgs_list_ori.write(pkg.text + "\n")

    # delete repeated packages
    with open(rpm_list_uniq, "w") as pkgs_list_uniq:
        with open(rpm_list, "r") as pkgs_list_ori:
            lines_met = set()
            for line in pkgs_list_ori:
                if line not in lines_met:
                    pkgs_list_uniq.write(line)
                    lines_met.add(line)
    os.remove(rpm_list)

    tmp_dir = os.path.join(common_vars.BUILD, "tmp")
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)

    # delete files that outdate
    if os.path.isfile("not_find.txt"):
        os.remove("not_find.txt")
    for invalid_file in glob.glob("*_pkg_*txt"):
        if os.path.isfile(invalid_file):
            os.remove(invalid_file)

    # get list of all available packages
    cmd = "yum list --installroot=" + os.path.join(common_vars.BUILD, "tmp") + " available"
    fo = open(list_log, "w")
    subprocess.call(cmd, shell = True, stdout = fo)
    fo.close()
    fr = open(list_log, "r")
    fo = open(yum_pkg_avail, "w")
    for line in fr:
        linelist = re.split(r'[\s]',line)
        fo.write(linelist[0] + "\n")
    fo.close()
    fr.close()
    os.remove(list_log)

    # show the packages that can not find in repo
    if get_down_pkg(yum_pkg_avail, rpm_list_uniq, common_vars.ARCH) == 1:
        with open("not_find.txt","r") as not_find:
            lines_met = set()
            for line in not_find:
                line = line.strip("\n")
                if line not in lines_met:
                    print(line)
                    lines_met.add(line)

    # get exclude list 
    conflict_pkgs = ""
    if "CONFIG_EXCLUDE_LIST" in common_vars.config_dict:
        with open(common_vars.config_dict.get("CONFIG_EXCLUDE_LIST"), "r") as exclude_pkg:
            for line in exclude_pkg:
                conflict_pkgs += line.replace("\n", " ")

    # get all packages to one line
    pkgs_to_down = ""
    with open("down_list.txt", "r") as down_list:
        for line in down_list:
            pkgs_to_down += line.replace("\n", " ")

    # download the pacakges
    with open("yum_down_log.txt", "w") as yum_down_log:
        if conflict_pkgs:
            cmd = "yumdownloader --resolve --installroot=" + os.path.join(common_vars.BUILD, "tmp") \
                    + "tmp --destdir=" + os.path.join(common_vars.BUILD, "iso/Packages/") + \
                    " " + pkgs_to_down + " -x " + conflict_pkgs
        else:
            cmd = "yumdownloader --resolve --installroot=" + os.path.join(common_vars.BUILD, "tmp") \
                    + "tmp --destdir=" + os.path.join(common_vars.BUILD, "iso/Packages/") + \
                    " " + pkgs_to_down
        res = subprocess.run(cmd, shell = True, stdout = yum_down_log, stderr = yum_down_log)

    if res.returncode != 0 or CF.search_str(yum_down_log, "conflicting requests"):
        CF.print_file("yum_down_log.txt")
        raise RuntimeError("Download rpms failed!", res)

    CF().print_file("yum_down_log.txt")

    if "CONFIG_CONFLICT" in common_vars.config_dict:
        conflict_pkgs_to_down = ""
        with open(common_vars.config_dist.get("CONFIG_CONFLICT"), "r") as conflict_pkg:
            for line in conflict_pkg:
                conflict_pkgs_to_down += line.replace("\n", " ")
                if conflict_pkgs:
                    cmd = "yumdownloader --resolve --installroot=" + os.path.join(common_vars.BUILD, "tmp") \
                            + " --destdir=" + os.path.join(common_vars.BUILD, "iso/Packages/") + \
                            " " + conflict_pkgs_to_down + " -x " + conflict_pkgs
                else:
                    cmd = "yumdownloader --resolve --installroot=" + os.path.join(common_vars.BUILD, "tmp") \
                            + " --destdir=" + os.path.join(common_vars.BUILD, "iso/Packages/") + \
                            " " + conflict_pkgs_to_down
        subprocess.run(cmd, shell = True)

    """
    if common_vars.DBG_FLAG:
        #TO BE DONE
        print("to be done")
    """

    # create local repo
    repo_dir = os.path.join(common_vars.BUILD, "iso/repodata/")
    iso_dir = os.path.join(common_vars.BUILD, "iso")
    os.makedirs(repo_dir)
    shutil.copy(common_vars.config_dist.get("CONFIG_PACKAGES_LIST_FILE"), repo_dir)
    cmd = "createrepo -g " + repo_dir + "*.xml" + " " + iso_dir
    subprocess.run(cmd, shell = True)

# get rpm public key and put it to iso
def get_rpm_pub_key(BUILD_dir):
    iso_dir = os.path.join(BUILD_dir, "iso/")
    GPG_tmpdir = os.path.join(BUILD_dir, "iso/GPG_tmp/")
    if os.path.isdir(GPG_tmpdir):
        shutil.rmtree(GPG_tmpdir)
    os.makedirs(GPG_tmpdir)
    GPG_pkg = glob.glob(os.path.join(BUILD_dir, "openEuler-gpg-keys*"))
    # check if there is gpg-keys pcakges
    if GPG_pkg == []:
        raise RuntimeError("no openEuler-gpg-keys")
    shutil.copy(GPG_pkg[0], GPG_tmpdir)
    # get the current working directory
    working_dir = os.getcwd()
    # change to the temporary dir that extract rpm to it
    os.chdir(GPG_tmpdir)
    cmd = "rpm2cpio " + GPG_pkg[0] + " | cpio -di"
    subprocess.run(cmd, shell = True)
    GPG_file = os.path.join(GPG_tmpdir, "etc/pki/rpm-gpg/RPM-GPG-KEY-openEuler")
    shutil.copy(GPG_file, iso_dir)
    os.chdir(working_dir)
    #clean temp dir
    shutil.rmtree(GPG_tmpdir)


if __name__ == "__main__":
    pass
