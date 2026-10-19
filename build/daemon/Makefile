CC = gcc
CFLAGS = -Wall -Wextra -O2
LDFLAGS = -ldl

all: nexus-manager sys_stat.so

nexus-manager: nexus-manager.c
	$(CC) $(CFLAGS) -o nexus-manager nexus-manager.c $(LDFLAGS)

sys_stat.so: sys_stat.c
	$(CC) $(CFLAGS) -fPIC -shared -o sys_stat.so sys_stat.c

clean:
	rm -f nexus-manager sys_stat.so
