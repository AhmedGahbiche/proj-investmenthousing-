"""
System dependency checker for validating external tool availability.
Ensures OCR, image processing, and document parsing tools are properly installed.
"""
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DependencyChecker:
    """Validates system-level and Python dependencies for document processing."""
    
    # System commands that must be available
    SYSTEM_DEPENDENCIES = {
        'tesseract': {
            'command': 'tesseract',
            'version_flag': '--version',
            'required_for': 'PNG/image text extraction (OCR)',
            'install_help': 'Install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki'
        },
    }
    
    # Python packages that must be importable
    PYTHON_DEPENDENCIES = {
        'pdfplumber': 'PDF text extraction (primary)',
        'PyPDF2': 'PDF text extraction (fallback)',
        'docx': 'DOCX document parsing',
        'pytesseract': 'Python OCR interface',
        'PIL': 'Image processing',
        'sentence_transformers': 'Text embeddings',
        'sqlalchemy': 'Database ORM',
    }
    
    def __init__(self):
        """Initialize dependency checker."""
        self.system_check_results: Dict[str, bool] = {}
        self.python_check_results: Dict[str, bool] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def check_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Perform all dependency checks.
        
        Returns:
            Tuple of (all_critical_deps_available, warnings, errors)
        """
        logger.info("Starting system dependency checks...")
        
        # Check system dependencies
        self._check_system_dependencies()
        
        # Check Python dependencies
        self._check_python_dependencies()
        
        # Compile results
        all_available = all(self.system_check_results.values()) and \
                       all(self.python_check_results.values())
        
        return all_available, self.warnings, self.errors
    
    def _check_system_dependencies(self):
        """Check for required system commands."""
        logger.info("Checking system dependencies...")
        
        for dep_name, dep_info in self.SYSTEM_DEPENDENCIES.items():
            available = self._check_command_exists(dep_info['command'])
            self.system_check_results[dep_name] = available
            
            if not available:
                warning = f"⚠️  {dep_name} not found: {dep_info['install_help']}"
                self.warnings.append(warning)
                logger.warning(warning)
            else:
                logger.info(f"✓ {dep_name} is available")
    
    def _check_python_dependencies(self):
        """Check for required Python packages."""
        logger.info("Checking Python dependencies...")
        
        for package_name, use_case in self.PYTHON_DEPENDENCIES.items():
            available = self._check_package_importable(package_name)
            self.python_check_results[package_name] = available
            
            if not available:
                error = f"❌ {package_name} not installed (required for: {use_case})"
                self.errors.append(error)
                logger.error(error)
            else:
                logger.info(f"✓ {package_name} is available")
    
    @staticmethod
    def _check_command_exists(command: str) -> bool:
        """
        Check if a command exists in the system PATH.
        
        Args:
            command: Command name to check
            
        Returns:
            True if command is available, False otherwise
        """
        try:
            result = subprocess.run(
                [command, '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception as e:
            logger.warning(f"Error checking command {command}: {str(e)}")
            return False
    
    @staticmethod
    def _check_package_importable(package_name: str) -> bool:
        """
        Check if a Python package can be imported.
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if package is importable, False otherwise
        """
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"Error checking package {package_name}: {str(e)}")
            return False
    
    def get_status_report(self) -> str:
        """
        Generate a detailed status report of all dependencies.
        
        Returns:
            Formatted status report string
        """
        report = ["=" * 60]
        report.append("DEPENDENCY CHECK REPORT")
        report.append("=" * 60)
        
        # System dependencies
        report.append("\nSystem Dependencies:")
        for dep, status in self.system_check_results.items():
            status_symbol = "✓" if status else "✗"
            report.append(f"  {status_symbol} {dep}")
        
        # Python dependencies
        report.append("\nPython Packages:")
        for pkg, status in self.python_check_results.items():
            status_symbol = "✓" if status else "✗"
            report.append(f"  {status_symbol} {pkg}")
        
        # Warnings and errors
        if self.warnings:
            report.append("\nWarnings:")
            for warning in self.warnings:
                report.append(f"  {warning}")
        
        if self.errors:
            report.append("\nErrors:")
            for error in self.errors:
                report.append(f"  {error}")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_format_support_status(self) -> Dict[str, str]:
        """
        Get extraction capability for each document format.
        
        Returns:
            Dictionary mapping format -> support status
        """
        status = {
            'pdf': 'FULL' if self.python_check_results.get('pdfplumber', False) else 'PARTIAL',
            'docx': 'FULL' if self.python_check_results.get('docx', False) else 'UNAVAILABLE',
            'txt': 'FULL',  # Always supported, no dependencies
            'png': 'FULL' if (self.system_check_results.get('tesseract', False) and
                             self.python_check_results.get('pytesseract', False)) else 'UNAVAILABLE'
        }
        return status


# Global dependency checker instance
dependency_checker = DependencyChecker()
