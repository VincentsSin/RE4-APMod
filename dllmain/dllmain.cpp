#include <iostream>
#include <fstream>
#include "dllmain.h"
#include "AutoUpdater.h"
#include "ConsoleWnd.h"
#include "Settings.h"
#include "Game.h"
#include "input.hpp"
#include "gitparams.h"
#include "resource.h"
#include "Trainer.h"
#include "UI_DebugWindows.h"
#include "../wrappers/wrappers.h"

HMODULE g_module_handle = nullptr;

void Init_Main()
{
	con.log("Big ironic thanks to QLOC S.A.");

	// Get game pointers and version info
	if (!re4t::init::Game())
		return;
	
	// Make sure steam_appid.txt exists
	if (!std::filesystem::exists("steam_appid.txt") && std::filesystem::exists("bio4.exe"))
	{
		std::ofstream appid("steam_appid.txt");
		appid << "254700";
		appid.close();
	}

	// Initial logging
	std::string commit = GIT_CUR_COMMIT;
	commit.resize(8);

	spd::log()->info("Starting re4_ap_mod v{1}-{0}-{0}", APP_VERSION, commit, GIT_BRANCH);
	spd::LogProcessNameAndPID();
	spd::log()->info("Running from: \"{}\"", WstrToStr(rootPath));
	spd::log()->info("Game version: {}", GameVersion());

	// Detected if the HD Project is being used and apply changes needed by it
	const std::string bio4Path = std::filesystem::canonical(rootPath).parent_path().string() + "\\BIO4\\";
	const std::string doorse012_xsb_path = bio4Path + "snd\\doorse012.xsb";
	const std::string doorse012_xwb_path = bio4Path + "snd\\doorse012.xwb";

	if (std::filesystem::exists(doorse012_xsb_path) && std::filesystem::exists(doorse012_xwb_path))
	{
		#ifdef VERBOSE
		con.log("RE4 HD Project detected");
		#endif

		spd::log()->info("RE4 HD Project detected");

		re4ap::cfg->bIsUsingHDProject = true;
		re4ap::init::HDProject();
	}

	// Init input-related hooks and populate keymap (needed before we ReadSettings(), otherwise, parsing hotkeys will fail)
	pInput->init();

	// Read re4_tweaks settings
	re4ap::cfg->ReadConnection();
}

// Dll main function
bool APIENTRY DllMain(HMODULE hModule, DWORD fdwReason, LPVOID lpReserved)
{
	UNREFERENCED_PARAMETER(lpReserved);

	switch (fdwReason)
	{
	case DLL_PROCESS_ATTACH:

		g_module_handle = hModule;

		Init_Wrappers();

		re4t::init::ExceptionHandler();

		Init_Main();

		break;
	case DLL_PROCESS_DETACH:
		break;
	}

	return true;
}
