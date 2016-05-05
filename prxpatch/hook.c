/*
 * Copyright 2010 by Coldbird
 * Copyright 2016 by Shiz
 *
 * hook.c - Import Hooking Functions
 *
 * This file is part of Adhoc Emulator.
 *
 * Adhoc Emulator is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Adhoc Emulator is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Adhoc Emulator.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <pspsysmem_kernel.h>
#include <psputilsforkernel.h>
#include <psputils.h>
#include <string.h>
#include "pspdefs.h"
#include "hook.h"


typedef struct {
    const char * name;
    unsigned short version;
    unsigned short attribute;
    unsigned char entLen;
    unsigned char varCount;
    unsigned short funcCount;
    unsigned int * fnids;
    unsigned int * funcs;
    unsigned int * vnids;
    unsigned int * vars;
} PspModuleImport;


PspModuleImport *find_import_lib(SceModule *module, const char *library) {
    if (!module || !library)
        return NULL;

    for (u32 x = 0; x < module->stub_size;) {
        PspModuleImport *import = (PspModuleImport *)((u32)module->stub_top + x);
        if (import->name && !strcmp(import->name, library))
            return import;
        x += (u32)import->entLen * 4;
    }

    return NULL;
}

u32 find_import_by_nid(SceModule *module, const char *library, u32 nid) {
    PspModuleImport *import = find_import_lib(module, library);
    if (!import)
        return 0;

    for (u32 x = 0; x < import->funcCount; x++)
        if (import->fnids[x] == nid)
            return (u32)&import->funcs[x * 2];

    return 0;
}

void api_hook_import(u32 address, void *function) {
    if (!address)
        return;

    /* asm: jump */
    *(unsigned int *) (address) = 0x08000000 | ((unsigned int) function & 0x0FFFFFFF) >> 2;

    /* asm: nop */
    *(unsigned int *) (address + 4) = 0;

    /* flush data and instruction cache. */
    sceKernelDcacheWritebackInvalidateRange((const void *) address, 8);
    sceKernelIcacheInvalidateRange((const void *) address, 8);
}

void api_hook_import_syscall(u32 address, void *function) {
    if (!address)
        return;

    /* asm: jr $ra */
    *(unsigned int *) (address) = 0x03E00008;

    /* asm: syscall number */
    *(unsigned int *) (address + 4) = (((sceKernelQuerySystemCall(function)) << 6) | 12);

    /* flush data and instruction cache */
    sceKernelDcacheWritebackInvalidateRange((const void *) address, 8);
    sceKernelIcacheInvalidateRange((const void *) address, 8);
}

int hook_import_by_nid(SceModule *module, const char *library, u32 nid, void *function, int syscall) {
    u32 stub = find_import_by_nid(module, library, nid);
    if (!stub)
        return -1;

    if (syscall)
        api_hook_import_syscall(stub, function);
    else
        api_hook_import(stub, function);
    return 0;
}
