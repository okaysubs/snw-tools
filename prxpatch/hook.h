/*
 * Copyright 2010 by Coldbird
 *           2016 by Shiz
 *
 * hook.h - Import Hooking Functions
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
#pragma once

#include <psploadcore.h>

int hook_import_by_nid(SceModule *module, const char *library, u32 nid, void *function, int syscall);
