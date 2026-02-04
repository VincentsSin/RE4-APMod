#pragma once

// Used by dllmain.rc

#define APP_NAME				"re4_ap_mod"
#define APP_MAJOR				1
#define APP_MINOR				0
#define APP_BUILDNUMBER			0
#define APP_REVISION			0
#define APP_COMPANYNAME			"VincentsSin"
#define APP_DESCRPTION			"Archipelago mod for the UHD port of Resident Evil 4"
#define APP_COPYRIGHT			"Copyright (C) 2026 VincentsSin"
#define APP_ORIGINALVERSION		"dinput8.dll"
#define APP_INTERNALNAME		"re4_ap_mod"

// Get APP_VERSION
#define _TO_STRING_(x) #x
#define _TO_STRING(x) _TO_STRING_(x)
#define APP_VERSION _TO_STRING(APP_MAJOR) "." _TO_STRING(APP_MINOR) "." _TO_STRING(APP_BUILDNUMBER) "." _TO_STRING(APP_REVISION)
