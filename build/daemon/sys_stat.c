#include <stdio.h>
#include <stdlib.h>

// Standard diagnostic module for NexusAudit cluster
void run_diagnostic(void) {
    printf("[sys_stat.so] Running system diagnostic routine...\n");
    system("uptime > /var/log/nexus/last_diagnostic.log 2>&1");
    system("free -m >> /var/log/nexus/last_diagnostic.log 2>&1");
}
