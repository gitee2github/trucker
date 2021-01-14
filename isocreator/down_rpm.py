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

def src_of_downed(downed_dir):
    src_list_file = "src_pkg.txt"
    if os.path.isfile(src_list_file):
        os.remove(src_list_file)
    # list the already down packages that needed by installation iso
    cmd = "ls " + downed_dir
    with open("downed_pkgs.txt", "w") as downed_pkgs:
        subprocess.run(cmd, shell = True, stdout = downed_pkgs, stderr = downed_pkgs)

    # record the source rpm
    src_met = set()
    # get the source rpm through rpm
    with open("downed_pkgs.txt", "r") as downed_pkgs:
        for line in downed_pkgs.readlines():
            line1 = re.sub(".rpm\n", "", line)
            with open("src_pkg_tmp.txt","w") as src_pkg_tmp:
                subprocess.run(["repoquery","-s",line1],stdout = src_pkg_tmp)
            with open("src_pkg_tmp.txt","r") as src_pkg_tmp:
                src_last_line = src_pkg_tmp.readlines()[-1]
                if src_last_line not in src_met:
                    with open(src_list_file, "a") as src_pkg:
                        src_pkg.write(src_last_line)
                        src_met.add(src_last_line)
    # delete temp file of src_pkg_tmp.txt
    if os.path.isfile("src_pkg_tmp.txt"):
        os.remove("src_pkg_tmp.txt")

    return src_met


# down src rpm
def down_src_rpm(common_vars):
    if os.path.isdir(common_vars.SRC_DIR):
        shutil.rmtree(common_vars.SRC_DIR)
    os.makedirs(common_vars.SRC_DIR)
    down_dir = os.path.join(common_vars.BUILD, "iso/Packages/")
    src_pkgs_to_down = ""
    src_of_downed(down_dir)
    src_list_of_downed = "src_pkg.txt"

    # get the src packages that need to be down
    if os.path.isfile(src_list_of_downed) and os.path.getsize(src_list_of_downed):
        with open(src_list_of_downed, "r") as src_list_fd:
            for line in src_list_fd:
                src_pkgs_to_down += re.sub(r".rpm\n$", " ", line)
    else:
        raise RuntimeError("No %s !"% src_list_of_downed)
    
    cmd = "yumdownloader --install=" + os.path.join(common_vars.BUILD, "tmp") + " --source" \
            + " --destdir=" + common_vars.SRC_DIR + " " + src_pkgs_to_down
    subprocess.run(cmd, shell = True)
    cmd = "yumdownloader kernel-source --install="  + os.path.join(common_vars.BUILD, "tmp") + \
            " --destdir=" + common_vars.SRC_DIR
    subprocess.run(cmd, shell = True)
    return 0

def down_dbg_rpm(common_vars, yum_pkg_avail):
    all_dbg_pkgs = "all_dbg_pkgs.txt"
    dbg_pkg_src_tmp = "dbg_pkg_src_tmp.txt"
    dbg_pkgs_to_down = "dbg_pkgs_to_down.txt"
    dbg_pkgs_line = ""

    # delete the dbg_pkgs_to_down.txt generated before
    if os.path.isfile(dbg_pkgs_to_down):
        os.remove(dbg_pkgs_to_down)

    # get all available debuginfo packages list
    with open(yum_pkg_avail, "r") as all_avail_pkgs:
        with open(all_dbg_pkgs, "w") as all_dbg_pkgs_w:
            for line in all_avail_pkgs.readlines():
                if "-debuginfo" in line:
                    all_dbg_pkgs_w.write(line)
    # get the source rpm list of downed rpm packages
    down_dir = os.path.join(common_vars.BUILD, "iso/Packages/")
    src_met = src_of_downed(down_dir)

    # get the list of debuginfo that needed to be downed
    with open(all_dbg_pkgs, "r") as all_dbg_pkgs:
        for line in all_dbg_pkgs.readlines():
            with open(dbg_pkg_src_tmp,"w") as dbg_pkg_src_tmp_w:
                subprocess.run(["repoquery", "-s", line.strip("\n")], 
                        stdout = dbg_pkg_src_tmp_w, stderr = dbg_pkg_src_tmp_w)
            with open(dbg_pkg_src_tmp,"r") as dbg_pkg_src_tmp_r:
                if dbg_pkg_src_tmp_r.readlines()[-1] in src_met:
                    with open(dbg_pkgs_to_down, "a") as dbg_pkgs_to_down_a:
                        dbg_pkgs_to_down_a.write(line)

    # put all debuginfo packages into oneline for download
    with open(dbg_pkgs_to_down, "r") as dbg_pkgs_to_down_r:
        for line in dbg_pkgs_to_down_r.readlines():
            dbg_pkgs_line += re.sub(r"\n$", " ", line)

    # delete temp files of dbg_pkg_src_tmp.txt
    if os.path.isfile("dbg_pkg_src_tmp.txt"):
        os.remove("dbg_pkg_src_tmp.txt")

    cmd = "yumdownloader --resolve --install=" + os.path.join(common_vars.BUILD, "tmp") \
            + " --destdir=" + common_vars.DBG_DIR + " " + dbg_pkgs_line
    res = subprocess.run(cmd, shell = True)
    if res.returncode != 0:
        raise RuntimeError("Download debuginfo failed!", res)

# get rpm packages name for downloading
# yum_pkg_avail:yum list to get all the available pkgs
# rpm_list_uniq:pkgs to be done
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
                    rname_arch = rname + "." + specific_arch
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
            # if rname is not in available package list
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
                        # get the rpm packages that contain the rname
                        else:
                            with open("down_list.txt", "a") as down_list:
                                down_list.write(last_line)
                            continue
                # file exist but empty
                else:
                    with open("not_find.txt", "a") as not_find:
                        not_find.write("can not find %s in your repo\n" % (rname))
                    not_found_flag = 1
                    os.remove("query_pkg.txt")
                    continue

    return not_found_flag

### get rpm packages to be downloaded for standard iso from config/normal.xml
### and rpmlist.xml
### TO DO: the path of config file is relative path, maybe replaced by absolute path
def get_standard_pkglist(rpm_list, common_vars):
    # get the packages to be downloaded from config/${RACH}/normal.xml
    normal_rpm_file = ET.parse(common_vars.config_dict.get("CONFIG_PACKAGES_LIST_FILE"))
    normal_pkg_list = normal_rpm_file.findall("./group/packagelist")
    with open(rpm_list, "w") as pkgs_list_ori:
        for normal_pkgs in normal_pkg_list:
            for normal_pkg in list(normal_pkgs):
                pkgs_list_ori.write(normal_pkg.text + "\n")
    # get the common and arch specific packages to be download from rpmlist.xml
    rpmlist_rpm_file =  ET.parse(common_vars.config_dict.get("CONFIG_RPM_LIST"))
    rpmlist_pkg_list = rpmlist_rpm_file.findall("./group/packagelist")
    with open(rpm_list, "a") as pkgs_list_ori:
        for rpmlist_pkgs in rpmlist_pkg_list:
            if rpmlist_pkgs.attrib['type'] == common_vars.ARCH:
                for rpmlist_pkg in list(rpmlist_pkgs):
                    pkgs_list_ori.write(rpmlist_pkg.text + "\n")
            elif rpmlist_pkgs.attrib['type'] == 'common':
                for rpmlist_pkg in list(rpmlist_pkgs):
                    pkgs_list_ori.write(rpmlist_pkg.text + "\n")

# download packages in xml
def download_rpms(common_vars):

    rpm_list = "rpm_list.txt"
    rpm_list_uniq = "rpm_list_uniq.txt"
    list_log = "list_pkg_log.txt"
    yum_pkg_avail = "yum_pkg_avail.txt"

    # get rpm packages from .xml
    # TO DO: replace the new with get_standard_pkglist
    get_standard_pkglist(rpm_list, common_vars)
    '''
    rpm_file = ET.parse(common_vars.config_dict.get("CONFIG_PACKAGES_LIST_FILE"))
    pkg_list = rpm_file.findall("./group/packagelist")
    with open(rpm_list, "w") as pkgs_list_ori:
        for pkgs in pkg_list:
            for pkg in list(pkgs):
                pkgs_list_ori.write(pkg.text + "\n")
    '''

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
                    + " --destdir=" + os.path.join(common_vars.BUILD, "iso/Packages/") + \
                    " " + pkgs_to_down + " -x " + conflict_pkgs
        else:
            cmd = "yumdownloader --resolve --installroot=" + os.path.join(common_vars.BUILD, "tmp") \
                    + " --destdir=" + os.path.join(common_vars.BUILD, "iso/Packages/") + \
                    " " + pkgs_to_down
        res = subprocess.run(cmd, shell = True, stdout = yum_down_log, stderr = yum_down_log)

    if res.returncode != 0 or CF().search_str("yum_down_log.txt", "conflicting requests"):
        CF().print_file("yum_down_log.txt")
        raise RuntimeError("Download rpms failed!", res)

    CF().print_file("yum_down_log.txt")

    if "CONFIG_CONFLICT" in common_vars.config_dict:
        conflict_pkgs_to_down = ""
        with open(common_vars.config_dict.get("CONFIG_CONFLICT"), "r") as conflict_pkg:
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

    if common_vars.ISOTYPE == "debug":
        down_dbg_rpm(common_vars, yum_pkg_avail)
    elif common_vars.ISOTYPE == "source":
        down_src_rpm(common_vars)
        

    # create local repo
    repo_dir = os.path.join(common_vars.BUILD, "iso/repodata/")
    iso_dir = os.path.join(common_vars.BUILD, "iso")
    os.makedirs(repo_dir)
    shutil.copy(common_vars.config_dict.get("CONFIG_PACKAGES_LIST_FILE"), repo_dir)
    cmd = "createrepo -g " + repo_dir + "*.xml" + " " + iso_dir
    subprocess.run(cmd, shell = True)

# get rpm public key and put it to iso
def get_rpm_pub_key(BUILD_dir):
    iso_dir = os.path.join(BUILD_dir, "iso/")
    pkg_dir = os.path.join(BUILD_dir, "iso/Packages/")
    GPG_tmpdir = os.path.join(BUILD_dir, "iso/GPG_tmp/")
    if os.path.isdir(GPG_tmpdir):
        shutil.rmtree(GPG_tmpdir)
    os.makedirs(GPG_tmpdir)
    GPG_pkg = glob.glob(os.path.join(pkg_dir, "openEuler-gpg-keys*"))
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
