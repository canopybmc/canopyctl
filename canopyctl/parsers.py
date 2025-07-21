"""
Configuration and recipe file parsers for canopyctl.
"""

from pathlib import Path
from typing import Dict, List


class ConfigurationParser:
    """Parser for configuration files and recipe files."""
    
    @staticmethod
    def parse_conf_file(conf_file: Path) -> Dict[str, str]:
        """Parse a configuration file for relevant variables."""
        variables = {}
        target_vars = {'PACKAGECONFIG', 'DISTRO_FEATURES', 'PREFERRED_VERSION'}
        
        try:
            with open(conf_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    for var in target_vars:
                        if line.startswith(f"{var} ") or line.startswith(f"{var}="):
                            if '=' in line:
                                value = line.split('=', 1)[1].strip().strip('"\'')
                                variables[var] = value
                                break
        except Exception:
            pass
        
        return variables

    @staticmethod
    def parse_recipe_file(recipe_file: Path) -> Dict[str, str]:
        """Parse a recipe file for PACKAGECONFIG variables."""
        variables = {}
        
        try:
            with open(recipe_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if line.startswith('PACKAGECONFIG'):
                        if '=' in line:
                            value = line.split('=', 1)[1].strip().strip('"\'')
                            variables['PACKAGECONFIG'] = value
                        break
        except Exception:
            pass
        
        return variables


class RecipeAnalyzer:
    """Analyzer for recipe files and systemd services."""
    
    @staticmethod
    def find_recipe_files(recipe_name: str, meta_layers: List[Path]) -> List[Path]:
        """Find .bb and .bbappend files for a recipe."""
        recipe_files = []
        
        for layer in meta_layers:
            # Look for .bb files
            for bb_file in layer.rglob(f"{recipe_name}_*.bb"):
                recipe_files.append(bb_file)
            for bb_file in layer.rglob(f"{recipe_name}.bb"):
                recipe_files.append(bb_file)
            
            # Look for .bbappend files
            for bbappend_file in layer.rglob(f"{recipe_name}_*.bbappend"):
                recipe_files.append(bbappend_file)
            for bbappend_file in layer.rglob(f"{recipe_name}.bbappend"):
                recipe_files.append(bbappend_file)
        
        return list(set(recipe_files))

    @staticmethod
    def find_systemd_services(recipe_name: str, recipe_files: List[Path]) -> List[str]:
        """Find systemd services installed by the recipe."""
        services = []
        
        for recipe_file in recipe_files:
            try:
                with open(recipe_file, 'r') as f:
                    content = f.read()
                    
                    # Look for systemd service files
                    if 'systemd' in content.lower():
                        # Parse for service file installations
                        lines = content.split('\n')
                        for line in lines:
                            if '.service' in line and ('install' in line.lower() or 'FILES' in line):
                                # Extract service names (simplified parsing)
                                import re
                                matches = re.findall(r'(\w+\.service)', line)
                                services.extend(matches)
            except Exception:
                continue
        
        return list(set(services))