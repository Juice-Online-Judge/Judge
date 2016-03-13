#include <err.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <libutil.h>
#include <sys/wait.h>
#include "mount.h"

void sighand(int);

void sighand(int signo){
    struct mount_info_s buf;
    if(signo == SIGTERM){
        umount_tmpfs("/usr/jails/run/1");
        exit(0);
    }else if(signo == SIGHUP){
        printf("reloading...\n");
        mount_info(&buf, "/usr/jails/run/1");
        printf("type: %s\n", buf.type);
        printf("from: %s\n", buf.from);
        printf("to: %s\n", buf.to);
    }else{
        printf("signal recieve: %s\n", sys_signame[signo]);
    }
}

int main(int argc, char **argv){
    int i;
    struct pidfh *pfh;
    struct mount_info_s buf;
    pid_t otherpid, childpid;

    pfh = pidfile_open("/var/run/bsdjudge.pid", 0600, &otherpid);
    if (pfh == NULL) {
        if (errno == EEXIST) {
            errx(EXIT_FAILURE, "Daemon already running, pid: %d.", otherpid);
        }
        warn("Cannot open or create pidfile");
    }

    if (daemon(1, 1) == -1) {
        warn("Cannot daemonize");
        pidfile_remove(pfh);
        exit(EXIT_FAILURE);
    }

    pidfile_write(pfh);

    for(i = 0; i < 100; i++) signal(i, sighand);

    mount_info(&buf, "/usr/jails/run/1");
    if(strcmp(buf.type, "tmpfs") == 0){
        umount_tmpfs("/usr/jails/run/1");
    }
    mount_tmpfs("/usr/jails/run/1", 33554432);

    while(1){
        sleep(1);
    }

     pidfile_remove(pfh);
     exit(EXIT_SUCCESS);
}
