import os
import sys
import re
import ctypes
import logging
import argparse
from requests import get

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def is_admin():
    """
    Checks if the current script is running with administrator privileges.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Error checking for administrator privileges: {e}")
        return False


def run_as_admin():
    """
    Re-runs the current script with administrator privileges.
    """
    if sys.version_info[0] == 3:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    else:
        logging.error("Unsupported Python version for running as admin.")
    sys.exit(0)


# Request headers for web requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.41"
}

PUBLIC_DESKTOP_PATH = r"C:\Users\Public\Desktop"


def get_file_list(directory_path, file_extension):
    """
    Recursively gets a list of files with a specific extension from a directory.
    """
    found_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(f".{file_extension}"):
                found_files.append(os.path.join(root, file))
    return found_files


def download_and_add_icon(shortcut_file_path):
    """
    Downloads and replaces the icon for a given Steam shortcut file.
    """
    if not shortcut_file_path or shortcut_file_path == "0":
        return

    try:
        with open(shortcut_file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
    except Exception as e:
        logging.error(f"Error reading shortcut file {shortcut_file_path}: {e}")
        return

    steam_id_match = re.search(r"URL=steam://rungameid/(\d+)", content)
    if not steam_id_match:
        logging.warning(f"Steam ID not found in {shortcut_file_path}. Skipping.")
        return
    steam_id = steam_id_match.group(1)

    icon_path_match = re.search(r"IconFile=(.*\\(.*\.ico))", content)
    if not icon_path_match:
        logging.error(f"Icon path not found in {shortcut_file_path}. Skipping.")
        return
    full_icon_path = icon_path_match.group(1)
    icon_name = icon_path_match.group(2)

    icon_download_url = f"https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/{steam_id}/{icon_name}"

    try:
        response = get(icon_download_url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    except Exception as e:
        logging.error(
            f"Error downloading icon for {shortcut_file_path} from {icon_download_url}: {e}"
        )
        return

    if response.status_code != 200:
        logging.error(
            f"{shortcut_file_path:<50} Icon download failed with status code {response.status_code}"
        )
        return

    try:
        with open(full_icon_path, "wb") as icon_file:
            icon_file.write(response.content)
        logging.info(f"{shortcut_file_path:<50} Icon fixed successfully.")
    except PermissionError:
        logging.error(
            f"{shortcut_file_path:<50} Permission Denied. Please close the file and run the program as administrator."
        )
        # Do not exit here, allow other files to be processed if possible
    except Exception as e:
        logging.error(f"Error writing icon to {full_icon_path}: {e}")


def get_shortcut_files(base_path):
    """
    Collects Steam shortcut files from the specified base path and public desktop.
    """
    logging.info(f"Searching for shortcuts in: {base_path}")
    local_shortcuts = get_file_list(base_path, "url")
    public_shortcuts = get_file_list(PUBLIC_DESKTOP_PATH, "url")

    all_shortcuts = local_shortcuts + public_shortcuts
    logging.info(f"Found {len(all_shortcuts)} Steam shortcuts.")
    return all_shortcuts, len(local_shortcuts)


def select_files_to_process(all_shortcuts, local_shortcut_count):
    """
    Allows the user to select which shortcut files to process.
    """
    print("0: All files")
    for i, file_path in enumerate(all_shortcuts):
        print(f"{i + 1}: {file_path}")
    print("\nPlease select files to modify (separate numbers with spaces):")

    try:
        user_input = input().strip()
        if not user_input:
            return [], 0  # No selection, return empty list

        num_list = list(map(int, user_input.split()))
    except ValueError:
        logging.error("Invalid input. Please enter numbers separated by spaces.")
        return [], 0

    if 0 in num_list:
        return all_shortcuts, local_shortcut_count
    else:
        selected_shortcuts = []
        for i in range(len(all_shortcuts)):
            if i + 1 in num_list:
                selected_shortcuts.append(all_shortcuts[i])
            else:
                selected_shortcuts.append("0")  # Mark as '0' to skip
        return selected_shortcuts, local_shortcut_count


def process_icons(base_path):
    """
    Main function to process and fix Steam shortcut icons.
    """
    all_shortcuts, local_shortcut_count = get_shortcut_files(base_path)
    if not all_shortcuts:
        logging.info("No Steam shortcuts found. Exiting.")
        return

    selected_shortcuts, _ = select_files_to_process(all_shortcuts, local_shortcut_count)

    if not selected_shortcuts or all(s == "0" for s in selected_shortcuts):
        logging.info("No files selected for processing. Exiting.")
        return

    print(
        "Individual file fix time is less than 1 second. If it takes too long, consider using a proxy or waiting patiently."
    )
    logging.info("Starting icon fix...\n")

    for i, shortcut_file in enumerate(selected_shortcuts):
        if shortcut_file != "0":
            download_and_add_icon(shortcut_file)

    logging.info("\nIcon fix complete!")


def main():
    parser = argparse.ArgumentParser(description="Fix Steam shortcut icons.")
    parser.add_argument(
        "-path", type=str, help="Manually set the folder path to search for shortcuts."
    )
    args = parser.parse_args()

    target_folder_path = args.path if args.path else os.getcwd()

    if not is_admin():
        logging.info(
            "Not running as administrator. Attempting to re-run with elevated privileges..."
        )
        run_as_admin()
        # The script will exit here and re-launch as admin.
        # The following code will only execute if already running as admin or if re-launch fails.
        return

    try:
        os.system("cls" if os.name == "nt" else "clear")  # Clear console
        logging.info("Starting Steam icon fixer...\n")
        process_icons(target_folder_path)
    except Exception as e:
        logging.error(f"An unexpected error occurred during icon fixing: {e}")
    finally:
        logging.info("\nFixing process finished.")
        print("\nIf you encounter any issues, please contact the author:")
        print("Github: https://github.com/Einck0/IconFix")
        input("Press Enter to exit...")  # Use input for pause


if __name__ == "__main__":
    main()
