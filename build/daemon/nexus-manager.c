#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <grp.h>
#include <dlfcn.h>
#include <errno.h>
#include <time.h>

#define SOCKET_PATH "/run/nexus/manager.sock"
#define MODULE_DIR_PREFIX "/usr/lib/nexus/modules/"
#define BUFFER_SIZE 4096

void log_msg(const char *msg) {
    time_t now = time(NULL);
    char tbuf[64];
    strftime(tbuf, sizeof(tbuf), "%Y-%m-%d %H:%M:%S", localtime(&now));
    printf("[%s] [nexus-manager] %s\n", tbuf, msg);
    fflush(stdout);
}

// Simple JSON field extractor for "action" and "module"
int get_json_str(const char *json, const char *key, char *out, size_t out_len) {
    char search_pattern[128];
    snprintf(search_pattern, sizeof(search_pattern), "\"%s\"", key);
    char *kpos = strstr(json, search_pattern);
    if (!kpos) return -1;

    char *colon = strchr(kpos + strlen(search_pattern), ':');
    if (!colon) return -1;

    char *val_start = strchr(colon, '\"');
    if (!val_start) return -1;
    val_start++; // skip quote

    char *val_end = strchr(val_start, '\"');
    if (!val_end) return -1;

    size_t len = val_end - val_start;
    if (len >= out_len) len = out_len - 1;
    strncpy(out, val_start, len);
    out[len] = '\0';
    return 0;
}

void handle_client(int client_fd) {
    char buffer[BUFFER_SIZE];
    memset(buffer, 0, sizeof(buffer));

    ssize_t bytes_read = read(client_fd, buffer, sizeof(buffer) - 1);
    if (bytes_read <= 0) {
        close(client_fd);
        return;
    }

    char action[64] = {0};
    if (get_json_str(buffer, "action", action, sizeof(action)) != 0) {
        const char *resp = "{\"status\": \"error\", \"message\": \"Missing action parameter\"}\n";
        write(client_fd, resp, strlen(resp));
        close(client_fd);
        return;
    }

    if (strcmp(action, "ping") == 0) {
        const char *resp = "{\"status\": \"ok\", \"message\": \"pong\"}\n";
        write(client_fd, resp, strlen(resp));
    } else if (strcmp(action, "status") == 0) {
        const char *resp = "{\"status\": \"ok\", \"service\": \"nexus-manager-daemon\", \"version\": \"2.4.1\", \"privilege\": \"root\"}\n";
        write(client_fd, resp, strlen(resp));
    } else if (strcmp(action, "rotate_logs") == 0) {
        log_msg("Executing scheduled audit log rotation...");
        system("mkdir -p /var/log/nexus/archive && touch /var/log/nexus/archive/rotated.log");
        const char *resp = "{\"status\": \"ok\", \"message\": \"Audit logs rotated\"}\n";
        write(client_fd, resp, strlen(resp));
    } else if (strcmp(action, "load_diagnostic") == 0) {
        char module_path[512] = {0};
        if (get_json_str(buffer, "module", module_path, sizeof(module_path)) != 0) {
            const char *resp = "{\"status\": \"error\", \"message\": \"Missing module parameter\"}\n";
            write(client_fd, resp, strlen(resp));
            close(client_fd);
            return;
        }

        char logbuf[600];
        snprintf(logbuf, sizeof(logbuf), "Received request to load diagnostic module: %s", module_path);
        log_msg(logbuf);

        // Security Validation: Ensure module belongs to official nexus module directory
        // NOTE: Flawed check: uses strncmp prefix without canonicalizing the path with realpath()!
        if (strncmp(module_path, MODULE_DIR_PREFIX, strlen(MODULE_DIR_PREFIX)) != 0) {
            log_msg("Security violation: Module path rejected (must start with /usr/lib/nexus/modules/)");
            const char *resp = "{\"status\": \"error\", \"message\": \"Access denied: Module must reside in /usr/lib/nexus/modules/\"}\n";
            write(client_fd, resp, strlen(resp));
            close(client_fd);
            return;
        }

        // Dynamically load the shared object
        void *handle = dlopen(module_path, RTLD_NOW);
        if (!handle) {
            char err_resp[1024];
            snprintf(err_resp, sizeof(err_resp), "{\"status\": \"error\", \"dlerror\": \"%s\"}\n", dlerror());
            write(client_fd, err_resp, strlen(err_resp));
        } else {
            void (*run_diagnostic)(void) = (void (*)(void)) dlsym(handle, "run_diagnostic");
            if (run_diagnostic) {
                run_diagnostic();
            }
            const char *resp = "{\"status\": \"ok\", \"message\": \"Diagnostic module loaded and executed successfully\"}\n";
            write(client_fd, resp, strlen(resp));
            dlclose(handle);
        }
    } else {
        const char *resp = "{\"status\": \"error\", \"message\": \"Unknown action\"}\n";
        write(client_fd, resp, strlen(resp));
    }

    close(client_fd);
}

int main() {
    int server_fd, client_fd;
    struct sockaddr_un addr;

    log_msg("Starting Nexus Core Privileged Management Daemon...");

    // Create /run/nexus directory if missing
    mkdir("/run/nexus", 0775);

    // Remove old socket if exists
    unlink(SOCKET_PATH);

    server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        exit(1);
    }

    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        exit(1);
    }

    // Assign group ownership to 'nexus' group so service user can interact
    struct group *grp = getgrnam("nexus");
    if (grp != NULL) {
        if (chown(SOCKET_PATH, 0, grp->gr_gid) != 0) {
            perror("chown socket");
        }
    }
    chmod(SOCKET_PATH, 0660);

    if (listen(server_fd, 10) < 0) {
        perror("listen");
        exit(1);
    }

    log_msg("IPC Socket listening on " SOCKET_PATH " (perms: 0660 root:nexus)");

    while (1) {
        client_fd = accept(server_fd, NULL, NULL);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }
        handle_client(client_fd);
    }

    close(server_fd);
    unlink(SOCKET_PATH);
    return 0;
}
