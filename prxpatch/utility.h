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
#pragma once

#include <psputility.h>
#include <psputility_savedata.h>

typedef struct SceUtilityScreenshotParam {
    pspUtilityDialogCommon base;
    char data[880];
} SceUtilityScreenshotParam;

int snw_save(SceUtilitySavedataParam *params);
