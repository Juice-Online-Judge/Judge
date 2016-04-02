#ifndef MOUNT_H
#define MOUNT_H

#include <sys/mount.h>

struct mount_info_s{
    char type[MFSNAMELEN];
    char from[MNAMELEN];
    char to[MNAMELEN];
};

int mount_prepare(char *, char *, size_t);
int mount_destroy(char *);
int mount_info(struct mount_info_s *, char *);
int mount_tmpfs(char *, size_t);
int umount_tmpfs(char *);
int mount_base(char *, char *);
int umount_base(char *);

#endif
