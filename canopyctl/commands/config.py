"""
Configuration commands for canopyctl.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ..core import CanopyCtl
from ..parsers import ConfigurationParser, RecipeAnalyzer


class ConfigShowCommand:
    """Command to show configuration information."""
    
    def __init__(self, canopyctl: CanopyCtl):
        self.canopyctl = canopyctl
        self.config_parser = ConfigurationParser()
        self.recipe_analyzer = RecipeAnalyzer()

    def execute(self, recipe_name: Optional[str] = None) -> int:
        """Execute the config show command."""
        print("=== Canopy Configuration Analysis ===\n")
        
        if not self.canopyctl.build_dir:
            print("Error: Could not find build directory with conf/local.conf")
            return 1
        
        print(f"Build Directory: {self.canopyctl.build_dir}")
        print(f"Meta Layers Found: {len(self.canopyctl.meta_layers)}")
        for layer in self.canopyctl.meta_layers:
            print(f"  - {layer}")
        print()
        
        if recipe_name:
            self._analyze_recipe(recipe_name)
        else:
            print("No recipe specified. Use: canopyctl config show <recipe-name>")
        
        self._show_global_config()
        return 0

    def _analyze_recipe(self, recipe_name: str):
        """Analyze a specific recipe."""
        print(f"=== Recipe Analysis: {recipe_name} ===")
        
        # Check if recipe is in current build
        recipe_included = self._is_recipe_included(recipe_name)
        print(f"Recipe included in build: {'YES' if recipe_included else 'NO'}")
        
        if recipe_included:
            # Find recipe files
            recipe_files = self.recipe_analyzer.find_recipe_files(
                recipe_name, self.canopyctl.meta_layers
            )
            print(f"Recipe files found: {len(recipe_files)}")
            for rf in recipe_files:
                print(f"  - {rf}")
            
            # Analyze systemd services
            systemd_services = self.recipe_analyzer.find_systemd_services(
                recipe_name, recipe_files
            )
            if systemd_services:
                print(f"Systemd services: {len(systemd_services)}")
                for service in systemd_services:
                    enabled = self._is_service_enabled(service)
                    print(f"  - {service} ({'enabled' if enabled else 'disabled'})")
            else:
                print("No systemd services found")
        print()

    def _is_recipe_included(self, recipe_name: str) -> bool:
        """Check if recipe is included in the current build."""
        # This would typically check bitbake's task dependencies or cache
        # For now, we'll check if recipe files exist in the layers
        recipe_files = self.recipe_analyzer.find_recipe_files(
            recipe_name, self.canopyctl.meta_layers
        )
        return len(recipe_files) > 0

    def _is_service_enabled(self, service: str) -> bool:
        """Check if a systemd service is enabled."""
        # This would typically check the rootfs or image configuration
        # For now, return a placeholder
        return True  # Simplified implementation

    def _show_global_config(self):
        """Show global configuration variables."""
        print("=== Global Configuration ===")
        
        config_vars = self._parse_configuration()
        
        for var_name in ['PACKAGECONFIG', 'DISTRO_FEATURES', 'PREFERRED_VERSION']:
            if var_name in config_vars:
                print(f"\n{var_name}:")
                for source, value in config_vars[var_name].items():
                    print(f"  {source}: {value}")
            else:
                print(f"\n{var_name}: Not found")

    def _parse_configuration(self) -> Dict[str, Dict[str, str]]:
        """Parse configuration from various sources."""
        config_vars = {}
        
        # Parse local.conf
        local_conf = self.canopyctl.build_dir / "conf" / "local.conf"
        if local_conf.exists():
            local_vars = self.config_parser.parse_conf_file(local_conf)
            for var, value in local_vars.items():
                if var not in config_vars:
                    config_vars[var] = {}
                config_vars[var]["local.conf"] = value
        
        # Parse machine conf files
        machine_conf_dir = self.canopyctl.build_dir / "conf" / "machine"
        if machine_conf_dir.exists():
            for conf_file in machine_conf_dir.glob("*.conf"):
                machine_vars = self.config_parser.parse_conf_file(conf_file)
                for var, value in machine_vars.items():
                    if var not in config_vars:
                        config_vars[var] = {}
                    config_vars[var][f"machine/{conf_file.name}"] = value
        
        # Parse distro conf files
        distro_conf_dir = self.canopyctl.build_dir / "conf" / "distro"
        if distro_conf_dir.exists():
            for conf_file in distro_conf_dir.glob("*.conf"):
                distro_vars = self.config_parser.parse_conf_file(conf_file)
                for var, value in distro_vars.items():
                    if var not in config_vars:
                        config_vars[var] = {}
                    config_vars[var][f"distro/{conf_file.name}"] = value
        
        # Parse recipe files for PACKAGECONFIG and PREFERRED_VERSION
        for layer in self.canopyctl.meta_layers:
            for bb_file in layer.rglob("*.bb"):
                recipe_vars = self.config_parser.parse_recipe_file(bb_file)
                for var, value in recipe_vars.items():
                    if var not in config_vars:
                        config_vars[var] = {}
                    config_vars[var][str(bb_file)] = value
        
        return config_vars