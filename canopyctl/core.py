"""
Core functionality for canopyctl.
"""

import os
from pathlib import Path
from typing import List, Optional


class CanopyCtl:
    """Main class for managing Canopy configurations."""
    
    def __init__(self):
        self.build_dir = self._find_build_directory()
        self.meta_layers = self._find_meta_layers()

    def _find_build_directory(self) -> Optional[Path]:
        """Find the Yocto/OpenEmbedded build directory."""
        current_dir = Path.cwd()
        
        # Check if we're already in a build directory
        if (current_dir / "conf" / "local.conf").exists():
            return current_dir
        
        # Look for build directory in common locations
        for build_name in ["build", "builds", "tmp"]:
            build_path = current_dir / build_name
            if (build_path / "conf" / "local.conf").exists():
                return build_path
        
        # Look in parent directories
        for parent in current_dir.parents:
            for build_name in ["build", "builds"]:
                build_path = parent / build_name
                if (build_path / "conf" / "local.conf").exists():
                    return build_path
        
        return None

    def _find_meta_layers(self) -> List[Path]:
        """Find meta layers in the project."""
        layers = []
        current_dir = Path.cwd()
        
        # Look for layers.txt or bblayers.conf
        if self.build_dir:
            bblayers_conf = self.build_dir / "conf" / "bblayers.conf"
            if bblayers_conf.exists():
                layers.extend(self._parse_bblayers_conf(bblayers_conf))
        
        # Fallback: look for meta-* directories
        for root_dir in [current_dir, current_dir.parent]:
            for item in root_dir.rglob("meta-*"):
                if item.is_dir() and (item / "conf" / "layer.conf").exists():
                    layers.append(item)
        
        return list(set(layers))

    def _parse_bblayers_conf(self, bblayers_conf: Path) -> List[Path]:
        """Parse bblayers.conf to extract layer paths."""
        layers = []
        try:
            with open(bblayers_conf, 'r') as f:
                in_bblayers = False
                for line in f:
                    line = line.strip()
                    if line.startswith('BBLAYERS'):
                        in_bblayers = True
                        continue
                    if in_bblayers:
                        if line.endswith('"'):
                            in_bblayers = False
                        if line and not line.startswith('#') and not line.startswith('BBLAYERS'):
                            layer_path = line.strip(' "\\\n')
                            if layer_path and Path(layer_path).exists():
                                layers.append(Path(layer_path))
        except Exception:
            pass
        return layers