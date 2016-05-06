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

#include <pspsdk.h>
#include "pspdefs.h"
#include "utility.h"

int (*sceUtilitySavedataInitStart_func)(SceUtilitySavedataParam * params) = NULL;

int snw_save(SceUtilitySavedataParam *params) {
    if (sceUtilitySavedataInitStart_func == NULL) {
        u32 k1 = pspSdkSetK1(0);
        sceUtilitySavedataInitStart_func = (void *)sctrlHENFindFunction("sceUtility_Driver", "sceUtility", 0x50C4CD57);
        pspSdkSetK1(k1);
    }

    params->base.language = PSP_SYSTEMPARAM_LANGUAGE_ENGLISH;
    return sceUtilitySavedataInitStart_func(params);
}
