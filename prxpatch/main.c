/*
 *  snwtlpatch kernel module
 *
 *  Copyright (C) 2011  Codestation
 *  Copyright (C) 2016  Shiz
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <pspkernel.h>
#include <psputilsforkernel.h>
#include <pspimpose_driver.h>
#include <string.h>
#include "pspdefs.h"
#include "hook.h"
#include "utility.h"

#define PLUGIN_NAME   "snwtlpatch"
#define GAME_MODULE   "soranowoto"
#define GAME_METAFILE "disc0:/UMD_DATA.BIN"


PSP_MODULE_INFO(PLUGIN_NAME, PSP_MODULE_KERNEL, 0, 5);
PSP_HEAP_SIZE_KB(0);


const char *game_ids[] = {
    "ULJM05673", /* Untranslated */
    "ULES05673", /* Translated */
    NULL
};

const struct {
    u32   nid;
    void *func;
} utility_stubs[] = {
    { 0x50C4CD57, snw_save  }, /* sceUtilitySavedataInitStart */
    { 0xF6269B82, snw_osk   }, /* sceUtilityOskInitStart */
    { 0x4DB1E739, snw_net   }, /* sceUtilityNetconfInitStart */
    { 0x0251B134, snw_shot  }, /* sceUtilityScreenshotInitStart */
    { 0,          NULL       }
};


int get_gameid(char *gameid) {
    SceUID fd = sceIoOpen(GAME_METAFILE, PSP_O_RDONLY, 0777);
    if (fd >= 0) {
        sceIoRead(fd, gameid, 10);
        sceIoClose(fd);

        /* Remove redundant -. */
        if (gameid[4] == '-') {
            memmove(gameid + 4, gameid + 5, 5);
        }
        gameid[9] = '\0';
    }
    return fd;
}

void patch_utility(SceModule *module) {
    for (u32 i = 0; utility_stubs[i].nid; i++) {
        hook_import_by_nid(module, "sceUtility", utility_stubs[i].nid, utility_stubs[i].func, 1);
    }
}

void change_lang(int lang) {
    int button;

    sceImposeGetLanguageMode((int[]){0}, &button);
    sceImposeSetLanguageMode(lang, button);
}

int thread_start(SceSize args, void *argp) {
    /* Get game ID. */
    char gameid[10];
    if (get_gameid(gameid) < 0)
        return 0;

    /* Check if this is our actual VN. */
    int match = 0;
    for (u32 i = 0; game_ids[i]; i++)
        if (!strcmp(gameid, game_ids[i]))
            match = 1;

    if (!match)
        return 0;

    /* Change the impose language. */
    change_lang(PSP_SYSTEMPARAM_LANGUAGE_ENGLISH);

    /* Patch utility hooks. */
    SceModule *module = sceKernelFindModuleByName(GAME_MODULE);
    if (module) {
        patch_utility(module);
    }

    return 0;
}

int module_start(SceSize args, void *argp) {
    SceUID thread = sceKernelCreateThread("snwtlpatch_main", thread_start, 0x22, 0x2000, 0, NULL);
    if (thread >= 0) {
        sceKernelStartThread(thread, args, argp);
    }
    return 0;
}

int module_stop(SceSize args, void *argp) {
    return 0;
}
