TARGET = snwtlpatch
OBJS =  main.o exports.o imports.o hook.o utility.o

LIBS =
WARN_FLAGS=-Wall -Wextra -Wfloat-equal -Wundef -Wshadow -Wpointer-arith -Wcast-align -Wwrite-strings -Wconversion -Wunreachable-code -Wno-unused-parameter
CFLAGS = -O2 -G0 -std=c99 $(WARN_FLAGS)
ASFLAGS = $(CFLAGS)

USE_KERNEL_LIBC = 1
USE_KERNEL_LIBS = 1

PSP_FW_VERSION=620

PSPSDK=$(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build_prx.mak
