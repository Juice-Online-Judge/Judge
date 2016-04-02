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
#include "signal.h"

int main(int argc, char **argv){
    int i;
    struct pidfh *pfh;
    struct mount_info_s buf;
    pid_t otherpid, childpid;

    pfh = pidfile_open("/var/run/bsdjudge.pid", 0600, &otherpid);
    if(pfh == NULL){
        if(errno == EEXIST){
            errx(EXIT_FAILURE, "Daemon already running, pid: %d.", otherpid);
        }
        warn("Cannot open or create pidfile");
    }

    if(daemon(1, 1) == -1){
        warn("Cannot daemonize");
        pidfile_remove(pfh);
        exit(EXIT_FAILURE);
    }

    pidfile_write(pfh);

    signal_init();

    mount_prepare("/usr/jails/base", "/usr/jails/run/1", 33554432);

    while(1){
        sleep(1);
    }

    pidfile_remove(pfh);
    exit(EXIT_SUCCESS);
}
