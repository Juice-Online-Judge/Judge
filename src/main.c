#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/wait.h>

void sighand(int signo){
    if(signo == SIGTERM){
        exit(0);
    }else if(signo == SIGHUP){
        printf("reloading...\n");
    }else{
        printf("signal recieve: %s\n", sys_signame[signo]);
    }
}

int main(int argc, char **argv){
    int i, pid;
    FILE *pidfile = NULL;
    if(fork() == 0){
        pid = fork();
        if(pid == 0){
            for(i = 0; i < 100; i++) signal(i, sighand);
            while(1){
                sleep(1);
            }
        }
        pidfile = fopen("/var/run/bsdjudge.pid", "w");
        if(pidfile != NULL){
            fprintf(pidfile, "%d\n", pid);
            fclose(pidfile);
        }
        exit(0);
    }
    wait(NULL);
    return 0;
}
