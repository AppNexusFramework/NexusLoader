"""
NexusSkyBase - Enhanced Module Loader
Supports loading from GitHub releases, URLs, or local zip files
"""

import os
import sys
import platform
import zipfile
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse


class NexusSkyBase:
    """
    Universal module loader for compiled Python modules.
    
    Supports loading from:
    - GitHub releases (version tags)
    - Direct URLs (zip files)
    - Local file paths (zip files)
    """
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        auto_install: bool = True,
        verbose: bool = True
    ):
        """
        Initialize NexusSkyBase.
        
        Args:
            cache_dir: Directory to store downloaded modules (default: ~/.nexus/bin)
            auto_install: Automatically install missing dependencies
            verbose: Print progress messages
        """
        self.verbose = verbose
        self.auto_install = auto_install
        
        # Setup cache directory
        if cache_dir is None:
            home = Path.home()
            self.cache_dir = home / ".nexus" / "bin"
        else:
            self.cache_dir = Path(cache_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect platform
        self.platform = self._detect_platform()
        
        # Add cache directory to Python path
        if str(self.cache_dir) not in sys.path:
            sys.path.insert(0, str(self.cache_dir))
        
        # Track loaded modules
        self.loaded_modules = {}
        
        self._log(f"Initialized NexusSkyBase")
        self._log(f"Platform: {self.platform}")
        self._log(f"Cache directory: {self.cache_dir}")
    
    def _log(self, message: str):
        """Print log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[NexusSkyBase] {message}")
    
    def _detect_platform(self) -> str:
        """Detect the current platform."""
        system = platform.system().lower()
        
        if system == "linux":
            return "linux"
        elif system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        else:
            raise OSError(f"Unsupported platform: {system}")
    
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _is_github_repo(self, source: str) -> bool:
        """Check if source is a GitHub repository URL."""
        return "github.com" in source and not source.endswith(".zip")
    
    def _download_file(self, url: str, destination: Path) -> bool:
        """
        Download a file from URL to destination.
        
        Args:
            url: URL to download from
            destination: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._log(f"Downloading from: {url}")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total size for progress
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if self.verbose:
                                progress = (downloaded / total_size) * 100
                                print(f"\rProgress: {progress:.1f}%", end="")
                    
                    if self.verbose:
                        print()  # New line after progress
            
            self._log(f"Downloaded successfully: {destination.name}")
            return True
            
        except requests.RequestException as e:
            self._log(f"Download failed: {e}")
            return False
        except Exception as e:
            self._log(f"Error during download: {e}")
            return False
    
    def _extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """
        Extract a zip file to the specified directory.
        
        Args:
            zip_path: Path to the zip file
            extract_to: Directory to extract to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._log(f"Extracting: {zip_path.name}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # List contents
                file_list = zip_ref.namelist()
                self._log(f"Archive contains {len(file_list)} files")
                
                # Extract all files
                zip_ref.extractall(extract_to)
            
            self._log(f"Extracted to: {extract_to}")
            return True
            
        except zipfile.BadZipFile:
            self._log(f"Error: Invalid zip file: {zip_path}")
            return False
        except Exception as e:
            self._log(f"Extraction failed: {e}")
            return False
    
    def _build_github_release_url(
        self,
        repo_url: str,
        version: str,
        release_name_template: str
    ) -> str:
        """
        Build GitHub release download URL.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
            version: Version tag (e.g., v1.0.0)
            release_name_template: Template for release filename (e.g., nexus-sky)
            
        Returns:
            Download URL for the release asset
        """
        # Clean repo URL
        repo_url = repo_url.rstrip('/')
        if repo_url.startswith('https://github.com/'):
            repo_url = repo_url.replace('https://github.com/', '')
        elif repo_url.startswith('github.com/'):
            repo_url = repo_url.replace('github.com/', '')
        
        # Build filename based on platform
        filename = f"{release_name_template}-{self.platform}-modules.zip"
        
        # Build full URL
        url = f"https://github.com/{repo_url}/releases/download/{version}/{filename}"
        
        return url
    
    def _install_from_github(
        self,
        repo_url: str,
        version: str,
        release_name_template: str
    ) -> bool:
        """
        Install modules from GitHub release.
        
        Args:
            repo_url: GitHub repository URL
            version: Version tag
            release_name_template: Template for release filename
            
        Returns:
            True if successful, False otherwise
        """
        # Build download URL
        download_url = self._build_github_release_url(
            repo_url, version, release_name_template
        )
        
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            # Download the release
            if not self._download_file(download_url, tmp_path):
                return False
            
            # Extract to cache directory
            if not self._extract_zip(tmp_path, self.cache_dir):
                return False
            
            return True
            
        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()
    
    def _install_from_url(self, url: str) -> bool:
        """
        Install modules from a direct URL to a zip file.
        
        Args:
            url: Direct URL to zip file
            
        Returns:
            True if successful, False otherwise
        """
        # Create temporary file for download
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            # Download the zip file
            if not self._download_file(url, tmp_path):
                return False
            
            # Extract to cache directory
            if not self._extract_zip(tmp_path, self.cache_dir):
                return False
            
            return True
            
        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()
    
    def _install_from_path(self, path: Union[str, Path]) -> bool:
        """
        Install modules from a local zip file.
        
        Args:
            path: Path to local zip file
            
        Returns:
            True if successful, False otherwise
        """
        zip_path = Path(path)
        
        if not zip_path.exists():
            self._log(f"Error: File not found: {zip_path}")
            return False
        
        if not zip_path.suffix.lower() == '.zip':
            self._log(f"Error: File is not a zip file: {zip_path}")
            return False
        
        # Extract to cache directory
        return self._extract_zip(zip_path, self.cache_dir)
    
    def install(
        self,
        source: str,
        version: Optional[str] = None,
        release_name_template: Optional[str] = None
    ) -> bool:
        """
        Install modules from various sources.
        
        Args:
            source: Can be:
                - GitHub repo URL (requires version and release_name_template)
                - Direct URL to zip file
                - Local path to zip file
            version: Version tag (only for GitHub repos)
            release_name_template: Release name template (only for GitHub repos)
            
        Returns:
            True if successful, False otherwise
            
        Examples:
            # From GitHub release
            install(
                "https://github.com/user/repo",
                version="v1.0.0",
                release_name_template="nexus-sky"
            )
            
            # From direct URL
            install("https://example.com/modules.zip")
            
            # From local file
            install("/path/to/modules.zip")
        """
        self._log(f"Installing from: {source}")
        
        # Determine source type and install
        if self._is_github_repo(source):
            # GitHub repository
            if not version or not release_name_template:
                self._log("Error: version and release_name_template required for GitHub repos")
                return False
            
            return self._install_from_github(source, version, release_name_template)
        
        elif self._is_url(source):
            # Direct URL
            return self._install_from_url(source)
        
        else:
            # Local file path
            return self._install_from_path(source)
    
    def load_module(self, module_name: str) -> Any:
        """
        Load a module by name.
        
        Args:
            module_name: Name of the module to load
            
        Returns:
            Loaded module object
        """
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]
        
        try:
            self._log(f"Loading module: {module_name}")
            module = __import__(module_name)
            self.loaded_modules[module_name] = module
            self._log(f"Successfully loaded: {module_name}")
            return module
            
        except ImportError as e:
            self._log(f"Failed to import {module_name}: {e}")
            raise
        except Exception as e:
            self._log(f"Error loading {module_name}: {e}")
            raise
    
    def get_class(self, module_name: str, class_name: str) -> type:
        """
        Get a class from a module.
        
        Args:
            module_name: Name of the module
            class_name: Name of the class
            
        Returns:
            Class object
        """
        module = self.load_module(module_name)
        
        if not hasattr(module, class_name):
            raise AttributeError(f"Module '{module_name}' has no class '{class_name}'")
        
        return getattr(module, class_name)
    
    def __getattr__(self, name: str) -> Any:
        """
        Dynamic attribute access for loaded modules.
        
        Allows: nexus.MyClass instead of nexus.get_class('module', 'MyClass')
        """
        # Try to find the class in any loaded module
        for module in self.loaded_modules.values():
            if hasattr(module, name):
                return getattr(module, name)
        
        # If not found in loaded modules, try to load it
        # This assumes the attribute name matches a module name
        try:
            return self.load_module(name)
        except:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    @classmethod
    def from_github(
        cls,
        repo_url: str,
        version: str,
        release_name_template: str,
        cache_dir: Optional[str] = None,
        auto_install: bool = True,
        verbose: bool = True
    ) -> 'NexusSkyBase':
        """
        Create NexusSkyBase instance and install from GitHub release.
        
        Args:
            repo_url: GitHub repository URL
            version: Version tag (e.g., "v1.0.0")
            release_name_template: Template for release filename (e.g., "nexus-sky")
            cache_dir: Custom cache directory
            auto_install: Automatically install if not present
            verbose: Print progress messages
            
        Returns:
            NexusSkyBase instance
            
        Example:
            nexus = NexusSkyBase.from_github(
                repo_url="https://github.com/user/repo",
                version="v1.0.0",
                release_name_template="nexus-sky"
            )
        """
        instance = cls(cache_dir=cache_dir, auto_install=auto_install, verbose=verbose)
        
        if auto_install:
            success = instance.install(repo_url, version, release_name_template)
            if not success:
                raise RuntimeError("Failed to install modules from GitHub")
        
        return instance
    
    @classmethod
    def from_url(
        cls,
        url: str,
        cache_dir: Optional[str] = None,
        auto_install: bool = True,
        verbose: bool = True
    ) -> 'NexusSkyBase':
        """
        Create NexusSkyBase instance and install from URL.
        
        Args:
            url: Direct URL to zip file
            cache_dir: Custom cache directory
            auto_install: Automatically install
            verbose: Print progress messages
            
        Returns:
            NexusSkyBase instance
            
        Example:
            nexus = NexusSkyBase.from_url(
                "https://example.com/modules.zip"
            )
        """
        instance = cls(cache_dir=cache_dir, auto_install=auto_install, verbose=verbose)
        
        if auto_install:
            success = instance.install(url)
            if not success:
                raise RuntimeError("Failed to install modules from URL")
        
        return instance
    
    @classmethod
    def from_path(
        cls,
        path: Union[str, Path],
        cache_dir: Optional[str] = None,
        auto_install: bool = True,
        verbose: bool = True
    ) -> 'NexusSkyBase':
        """
        Create NexusSkyBase instance and install from local path.
        
        Args:
            path: Path to local zip file
            cache_dir: Custom cache directory
            auto_install: Automatically install
            verbose: Print progress messages
            
        Returns:
            NexusSkyBase instance
            
        Example:
            nexus = NexusSkyBase.from_path(
                "/path/to/modules.zip"
            )
        """
        instance = cls(cache_dir=cache_dir, auto_install=auto_install, verbose=verbose)
        
        if auto_install:
            success = instance.install(path)
            if not success:
                raise RuntimeError("Failed to install modules from path")
        
        return instance
    
    @classmethod
    def from_tag(cls, *args, **kwargs) -> 'NexusSkyBase':
        """
        Alias for from_github() for backward compatibility.
        
        Deprecated: Use from_github() instead.
        """
        return cls.from_github(*args, **kwargs)
    
    def list_modules(self) -> list:
        """
        List all available module files in cache directory.
        
        Returns:
            List of module filenames
        """
        extensions = ['.so', '.pyd']
        modules = []
        
        for ext in extensions:
            modules.extend([
                f.stem for f in self.cache_dir.glob(f'*{ext}')
            ])
        
        return sorted(set(modules))
    
    def clear_cache(self) -> bool:
        """
        Clear the cache directory.
        
        Returns:
            True if successful
        """
        try:
            self._log(f"Clearing cache: {self.cache_dir}")
            
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self._log("Cache cleared successfully")
            
            return True
            
        except Exception as e:
            self._log(f"Failed to clear cache: {e}")
            return False

"""
# Example usage
if __name__ == "__main__":
    print("NexusSkyBase - Universal Module Loader")
    print("=" * 50)
    print()
    
    # Example 1: Load from GitHub release
    print("Example 1: Load from GitHub")
    print("-" * 50)
    try:
        nexus = NexusSkyBase.from_github(
            repo_url="https://github.com/user/nexus-modules",
            version="v1.0.0",
            release_name_template="nexus-sky"
        )
        print("✓ Loaded from GitHub successfully")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print()
    
    # Example 2: Load from direct URL
    print("Example 2: Load from URL")
    print("-" * 50)
    try:
        nexus = NexusSkyBase.from_url(
            "https://example.com/nexus-modules.zip"
        )
        print("✓ Loaded from URL successfully")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print()
    
    # Example 3: Load from local path
    print("Example 3: Load from local file")
    print("-" * 50)
    try:
        nexus = NexusSkyBase.from_path(
            "/path/to/modules.zip"
        )
        print("✓ Loaded from path successfully")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print()
    
    # Example 4: Universal install method
    print("Example 4: Universal install()")
    print("-" * 50)
    nexus = NexusSkyBase()
    
    # Can handle any source type
    sources = [
        ("GitHub", "https://github.com/user/repo", {"version": "v1.0.0", "release_name_template": "nexus"}),
        ("URL", "https://example.com/modules.zip", {}),
        ("Path", "/path/to/local/modules.zip", {})
    ]
    
    for name, source, kwargs in sources:
        print(f"\nTrying {name}: {source}")
        try:
            success = nexus.install(source, **kwargs)
            if success:
                print(f"  ✓ Installed successfully")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print()
    print("=" * 50)
    print("Examples complete!")
"""