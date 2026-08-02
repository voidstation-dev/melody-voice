import platform
import subprocess
import shutil
import os

def get_target_triple():
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":
        if machine in ("arm64", "aarch64"):
            return "aarch64-apple-darwin"
        else:
            return "x86_64-apple-darwin"
    elif system == "windows":
        return "x86_64-pc-windows-msvc"
    elif system == "linux":
        return "x86_64-unknown-linux-gnu"
    
    return "unknown"

def main():
    target_triple = get_target_triple()
    print(f"Detected target triple: {target_triple}")
    
    # Run PyInstaller
    subprocess.run([
        "pyinstaller",
        "--name", "melody-api",
        "--hidden-import=aiosqlite",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--distpath", "./dist",
        "app/main.py"
    ], check=True)
    
    # Copy to src-tauri/bin
    src_bin = "dist/melody-api"
    if platform.system().lower() == "windows":
        src_bin += ".exe"
        
    dest_dir = "../web/src-tauri/bin"
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_bin = f"{dest_dir}/melody-api-{target_triple}"
    if platform.system().lower() == "windows":
        dest_bin += ".exe"
        
    print(f"Copying {src_bin} to {dest_bin}")
    shutil.copy2(src_bin, dest_bin)
    print("Done!")

if __name__ == "__main__":
    main()
