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
int (*sceUtilityOskInitStart_func)(SceUtilityOskParams* params) = NULL;
int (*sceUtilityNetconfInitStart_func)(pspUtilityNetconfData *data) = NULL;
int (*sceUtilityScreenshotInitStart_func)(SceUtilityScreenshotParam *params) = NULL;

int snw_save(SceUtilitySavedataParam *params) {
    if (sceUtilitySavedataInitStart_func == NULL) {
        u32 k1 = pspSdkSetK1(0);
        sceUtilitySavedataInitStart_func = (void *)sctrlHENFindFunction("sceUtility_Driver", "sceUtility", 0x50C4CD57);
        pspSdkSetK1(k1);
    }

    params->base.language = PSP_SYSTEMPARAM_LANGUAGE_ENGLISH;
    return sceUtilitySavedataInitStart_func(params);
}

int snw_osk(SceUtilityOskParams *params) {
    if (sceUtilityOskInitStart_func == NULL) {
        u32 k1 = pspSdkSetK1(0);
        sceUtilityOskInitStart_func = (void *)sctrlHENFindFunction("sceUtility_Driver", "sceUtility", 0xF6269B82);
        pspSdkSetK1(k1);
    }

    params->base.language = PSP_SYSTEMPARAM_LANGUAGE_ENGLISH;
    params->data->language = PSP_UTILITY_OSK_LANGUAGE_JAPANESE;
    params->data->inputtype = PSP_UTILITY_OSK_INPUTTYPE_ALL;
    return sceUtilityOskInitStart_func(params);
}

int snw_net(pspUtilityNetconfData *data) {
    if (sceUtilityNetconfInitStart_func == NULL) {
        u32 k1 = pspSdkSetK1(0);
        sceUtilityNetconfInitStart_func = (void *)sctrlHENFindFunction("sceUtility_Driver", "sceUtility", 0x4DB1E739);
        pspSdkSetK1(k1);
    }

    data->base.language = PSP_SYSTEMPARAM_LANGUAGE_ENGLISH;
    return sceUtilityNetconfInitStart_func(data);
}

int snw_shot(SceUtilityScreenshotParam *params) {
    if (sceUtilityScreenshotInitStart_func == NULL) {
        u32 k1 = pspSdkSetK1(0);
        sceUtilityScreenshotInitStart_func = (void *)sctrlHENFindFunction("sceUtility_Driver", "sceUtility", 0x0251B134);
        pspSdkSetK1(k1);
    }

    params->base.language = PSP_SYSTEMPARAM_LANGUAGE_ENGLISH;
    return sceUtilityScreenshotInitStart_func(params);
}
