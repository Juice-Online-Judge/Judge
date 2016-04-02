#include "mount.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/uio.h>

static size_t build_iovec(struct iovec *, const char *, const char *);

int mount_prepare(char *from, char *path, size_t size){
    char buf[BUFSIZ];

    snprintf(buf, BUFSIZ, "%s/tmp", path);
    mount_base(from, path);
    mount_tmpfs(buf, size);
    return 0;
}

int mount_destroy(char *path){
    char buf[BUFSIZ];
    snprintf(buf, BUFSIZ, "%s/tmp", path);

    umount_tmpfs(buf);
    umount_base(path);
    return 0;
}

int mount_info(struct mount_info_s *mount_info, char *path){
    int ret;
    struct statfs ptr;
    ret = statfs(path, &ptr);
    if(ret == -1){
        perror("statfs");
    }else{
        strncpy(mount_info->type, ptr.f_fstypename, MFSNAMELEN);
        strncpy(mount_info->from, ptr.f_mntfromname, MNAMELEN);
        strncpy(mount_info->to, ptr.f_mntonname, MNAMELEN);
    }
    return ret;
}

int mount_tmpfs(char *path, size_t size){
    int ret;
    struct iovec iov[8];
    size_t iovlen = 0;
    char size_buf[32];

    snprintf(size_buf, 32, "%zu", size);
    iovlen += build_iovec(&iov[iovlen], "fstype", "tmpfs");
    iovlen += build_iovec(&iov[iovlen], "from", "tmpfs");
    iovlen += build_iovec(&iov[iovlen], "fspath", path);
    iovlen += build_iovec(&iov[iovlen], "size", size_buf);
    ret = nmount(iov, iovlen, 0);
    if(ret < 0){
        perror("nmount");
    }
    return ret;
}

int umount_tmpfs(char *path){
    int ret;
    ret = unmount(path, 0);
    return ret;
}

int mount_base(char *from, char *to){
    int ret;
    struct iovec iov[6];
    size_t iovlen = 0;

    iovlen += build_iovec(&iov[iovlen], "fstype", "nullfs");
    iovlen += build_iovec(&iov[iovlen], "target", from);
    iovlen += build_iovec(&iov[iovlen], "fspath", to);
    ret = nmount(iov, iovlen, MNT_RDONLY);
    if(ret < 0){
        perror("nmount");
    }
    return ret;
}

int umount_base(char *path){
    int ret;
    ret = unmount(path, 0);
    return ret;
}

static size_t build_iovec(struct iovec *iov, const char *name, const char *val){
    iov[0].iov_base = (void *)name;
    iov[0].iov_len = (size_t)strlen(name) + 1;
    iov[1].iov_base = (void *)val;
    iov[1].iov_len = (size_t)strlen(val) + 1;
    return 2;
}
