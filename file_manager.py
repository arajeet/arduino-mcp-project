import os

def dfs_walk(root_dir):
    """
    Performs a Depth-First Search on a given root directory to find all files and folders.

    Args:
        root_dir (str): The path to the starting directory.

    Returns:
        tuple: A tuple containing two lists: (all_files, all_folders).
               all_files: A list of full paths to all files found.
               all_folders: A list of full paths to all folders found.
    """
    all_files = []
    all_folders = []

    # Add the root directory itself to the folders list
    if os.path.isdir(root_dir):
        all_folders.append(root_dir)

    # Use a stack for iterative DFS (or recursion for a more direct approach)
    stack = [root_dir]

    while stack:
        current_path = stack.pop()

        try:
            # List all entries in the current directory
            for entry in os.listdir(current_path):
                full_path = os.path.join(current_path, entry)

                if os.path.isdir(full_path):
                    all_folders.append(full_path)
                    stack.append(full_path)  # Push folder onto stack for deeper exploration
                elif os.path.isfile(full_path):
                    all_files.append(full_path)
        except PermissionError:
            print(f"Permission denied for: {current_path}")
        except FileNotFoundError:
            print(f"Directory not found: {current_path}")

    return all_files, all_folders


files, folders = dfs_walk("Y:\MobileBackup\Arajeet's Z Fold5")
print("Files found:")
for f in files:
    print(f)
print("\nFolders found:")
for d in folders:
    print(d)