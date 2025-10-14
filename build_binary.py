#!/usr/bin/env python3
"""
Binary Builder Script
=====================
Converts Python scripts to standalone executables using PyInstaller

Usage:
    python build_binary.py <script_path> [--output-dir OUTPUT_DIR] [--name NAME]

Example:
    python build_binary.py nexus_etl.py --output-dir ./bin --name nexus-etl

Author: Mauro Tommasi
License: MIT
"""

import os
import sys
import argparse
import subprocess
import shutil
import platform
from pathlib import Path
import json


class BinaryBuilder:
    """Build standalone binaries from Python scripts"""
    
    def __init__(self, script_path: str, output_dir: str = "./bin", binary_name: str = None):
        self.script_path = Path(script_path)
        self.output_dir = Path(output_dir)
        self.binary_name = binary_name or self.script_path.stem
        self.platform = platform.system().lower()
        self.arch = platform.machine().lower()
        
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
    
    def build(self, one_file: bool = True, console: bool = True, icon: str = None):
        """Build the binary using PyInstaller"""
        print(f"Building binary for {self.script_path.name}...")
        print(f"Platform: {self.platform}")
        print(f"Architecture: {self.arch}")
        
        # Prepare PyInstaller command
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
        ]
        
        # One-file or one-folder
        if one_file:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")
        
        # Console or windowed
        if console:
            cmd.append("--console")
        else:
            cmd.append("--windowed")
        
        # Icon (Windows/Mac)
        if icon and os.path.exists(icon):
            cmd.extend(["--icon", icon])
        
        # Output name
        binary_suffix = self._get_binary_suffix()
        final_name = f"{self.binary_name}{binary_suffix}"
        cmd.extend(["--name", final_name])
        
        # Add hidden imports for common packages
        hidden_imports = [
            "pandas",
            "numpy",
            "requests",
            "cryptography",
            "boto3",
            "paramiko",
            "yaml",
            "json",
        ]
        
        for imp in hidden_imports:
            cmd.extend(["--hidden-import", imp])
        
        # Add the script
        cmd.append(str(self.script_path))
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            # Run PyInstaller
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("Build successful!")
            
            # Move binary to output directory
            self._move_binary_to_output(final_name)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def _get_binary_suffix(self) -> str:
        """Get platform-specific binary suffix"""
        if self.platform == "windows":
            return ".exe"
        elif self.platform == "darwin":
            return "-macos"
        elif self.platform == "linux":
            return f"-linux-{self.arch}"
        return ""
    
    def _move_binary_to_output(self, binary_name: str):
        """Move built binary to output directory"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find the built binary
        dist_dir = Path("dist")
        source_binary = dist_dir / binary_name
        
        if not source_binary.exists():
            # Try without extension
            source_binary = dist_dir / self.binary_name
        
        if source_binary.exists():
            # Destination
            dest_binary = self.output_dir / binary_name
            
            # Copy binary
            if source_binary.is_file():
                shutil.copy2(source_binary, dest_binary)
                # Make executable on Unix
                if self.platform in ["linux", "darwin"]:
                    os.chmod(dest_binary, 0o755)
            else:
                # Directory (one-folder mode)
                if dest_binary.exists():
                    shutil.rmtree(dest_binary)
                shutil.copytree(source_binary, dest_binary)
            
            print(f"Binary moved to: {dest_binary}")
            
            # Create version info file
            self._create_version_info(dest_binary.parent)
        else:
            print(f"Warning: Could not find built binary at {source_binary}")
    
    def _create_version_info(self, output_dir: Path):
        """Create version info file"""
        version_info = {
            "binary_name": self.binary_name,
            "script": str(self.script_path),
            "platform": self.platform,
            "architecture": self.arch,
            "build_date": subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip()
        }
        
        version_file = output_dir / "version.json"
        with open(version_file, "w") as f:
            json.dump(version_info, f, indent=2)
        
        print(f"Version info saved to: {version_file}")
    
    def clean(self):
        """Clean build artifacts"""
        print("Cleaning build artifacts...")
        
        for dir_name in ["build", "dist", "__pycache__"]:
            dir_path = Path(dir_name)
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"Removed: {dir_path}")
        
        # Remove .spec files
        for spec_file in Path(".").glob("*.spec"):
            spec_file.unlink()
            print(f"Removed: {spec_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Build standalone binaries from Python scripts"
    )
    parser.add_argument(
        "script",
        help="Path to Python script to build"
    )
    parser.add_argument(
        "--output-dir",
        default="./bin",
        help="Output directory for binary (default: ./bin)"
    )
    parser.add_argument(
        "--name",
        help="Binary name (default: script name)"
    )
    parser.add_argument(
        "--one-folder",
        action="store_true",
        help="Build as one-folder instead of one-file"
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Build as windowed app (no console)"
    )
    parser.add_argument(
        "--icon",
        help="Path to icon file (.ico for Windows, .icns for Mac)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts after build"
    )
    
    args = parser.parse_args()
    
    # Build binary
    builder = BinaryBuilder(args.script, args.output_dir, args.name)
    
    success = builder.build(
        one_file=not args.one_folder,
        console=not args.windowed,
        icon=args.icon
    )
    
    # Clean if requested
    if args.clean and success:
        builder.clean()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()