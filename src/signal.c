#include "signal.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "mount.h"

void signal_term(int);
void signal_hup(int);

int signal_init(){
    struct sigaction act;

    act.sa_flags = SA_RESTART;
    act.sa_sigaction = NULL;
    sigemptyset(&act.sa_mask);
    sigfillset(&act.sa_mask);

    act.sa_handler = signal_term;
    sigaction(SIGTERM, &act, NULL);
    act.sa_handler = signal_hup;
    sigaction(SIGHUP, &act, NULL);
    return 0;
}

void signal_term(int signo){
    mount_destroy("/usr/jails/run/1");
    exit(EXIT_SUCCESS);
}

void signal_hup(int signo){
    struct mount_info_s buf;
    printf("reloading...\n");
    mount_info(&buf, "/usr/jails/run/1");
    printf("type: %s\n", buf.type);
    printf("from: %s\n", buf.from);
    printf("to: %s\n", buf.to);
}
