import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Dict
import threading
from dataclasses import dataclass
from enum import Enum

class CleanupStrategy(Enum):
    # Different cleanup strategies
    CONSERVATIVE = "conservative"  # Keep more logs, slower cleanup
    BALANCED = "balanced"         # Default balanced approach
    AGGRESSIVE = "aggressive"     # Keep fewer logs, faster cleanup

@dataclass
class LogFileInfo:
    # Information about a log file
    path: Path
    size_bytes: int
    created_time: datetime
    modified_time: datetime
    age_hours: float
    
    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)
    
    @property
    def size_kb(self) -> float:
        return self.size_bytes / 1024

class SmartLogCleaner:
    # Intelligent log cleanup system with multiple strategies
    
    def __init__(self, log_directory: str = "logs", strategy: CleanupStrategy = CleanupStrategy.BALANCED):
        self.log_dir = Path(log_directory)
        self.strategy = strategy
        self.lock = threading.Lock()
        
        # Configuration based on strategy
        self.config = self._get_strategy_config(strategy)
        
        # Statistics
        self.stats = {
            "files_deleted": 0,
            "bytes_freed": 0,
            "last_cleanup": None,
            "total_cleanups": 0
        }
    
    def _get_strategy_config(self, strategy: CleanupStrategy) -> Dict:
        # Get configuration based on cleanup strategy
        configs = {
            CleanupStrategy.CONSERVATIVE: {
                "max_files": 100,           # Keep up to 100 files
                "max_total_size_mb": 50,    # Keep up to 50MB total
                "min_keep_files": 20,       # Always keep at least 20 files
                "max_age_days": 30,         # Delete files older than 30 days
                "size_threshold_mb": 5,     # Delete large files (>5MB) more aggressively
                "keep_recent_hours": 24,    # Always keep files from last 24 hours
                "cleanup_interval_hours": 24 # Run cleanup every 24 hours
            },
            CleanupStrategy.BALANCED: {
                "max_files": 50,            # Keep up to 50 files
                "max_total_size_mb": 20,    # Keep up to 20MB total
                "min_keep_files": 10,       # Always keep at least 10 files
                "max_age_days": 14,         # Delete files older than 14 days
                "size_threshold_mb": 2,     # Delete large files (>2MB) more aggressively
                "keep_recent_hours": 12,    # Always keep files from last 12 hours
                "cleanup_interval_hours": 12 # Run cleanup every 12 hours
            },
            CleanupStrategy.AGGRESSIVE: {
                "max_files": 10,            # Keep up to 10 files
                "max_total_size_mb": 5,     # Keep up to 5MB total
                "min_keep_files": 3,        # Always keep at least 3 files
                "max_age_days": 3,          # Delete files older than 3 days
                "size_threshold_mb": 0.5,   # Delete large files (>0.5MB) more aggressively
                "keep_recent_hours": 6,   # Always keep files from last 6 h
                "cleanup_interval_hours": 2  # Run cleanup every 2 hours
            }
        }
        return configs[strategy]
    
    def scan_log_files(self) -> List[LogFileInfo]:
        # Scan and analyze all log files
        if not self.log_dir.exists():
            return []
        
        log_files = []
        current_time = datetime.now()
        
        for file_path in self.log_dir.glob("*.log"):
            try:
                stat = file_path.stat()
                created_time = datetime.fromtimestamp(stat.st_ctime)
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                age_hours = (current_time - modified_time).total_seconds() / 3600
                
                log_info = LogFileInfo(
                    path=file_path,
                    size_bytes=stat.st_size,
                    created_time=created_time,
                    modified_time=modified_time,
                    age_hours=age_hours
                )
                log_files.append(log_info)
            except (OSError, ValueError) as e:
                print(f"Error scanning {file_path}: {e}")
                continue
        
        return log_files
    
    def calculate_cleanup_priority(self, log_files: List[LogFileInfo]) -> List[Tuple[LogFileInfo, float]]:
        # Calculate cleanup priority for each file (higher score = higher priority for deletion)
        priorities = []
        
        for log_file in log_files:
            score = 0.0
            
            # Age factor (older files get higher score)
            age_factor = min(log_file.age_hours / (self.config["max_age_days"] * 24), 2.0)
            score += age_factor * 40
            
            # Size factor (larger files get higher score)
            if log_file.size_mb > self.config["size_threshold_mb"]:
                size_factor = min(log_file.size_mb / self.config["size_threshold_mb"], 3.0)
                score += size_factor * 30
            
            # Empty or very small files get higher score
            if log_file.size_bytes < 1024:  # Less than 1KB
                score += 50
            
            # Files with duplicate timestamps (failed starts) get higher score
            timestamp_str = log_file.path.stem.split('_')[-2:]  # Extract date and time
            if len(timestamp_str) == 2:
                try:
                    file_time = datetime.strptime('_'.join(timestamp_str), '%Y%m%d_%H%M%S')
                    # If file is much older than its timestamp suggests, it might be a duplicate
                    time_diff = abs((log_file.modified_time - file_time).total_seconds())
                    if time_diff > 3600:  # More than 1 hour difference
                        score += 20
                except ValueError:
                    pass
            
            # Recent files get negative score (protection)
            if log_file.age_hours < self.config["keep_recent_hours"]:
                score -= 100  # Strong protection for recent files
            
            priorities.append((log_file, score))
        
        # Sort by priority (highest score first)
        return sorted(priorities, key=lambda x: x[1], reverse=True)
    
    def should_cleanup(self, log_files: List[LogFileInfo]) -> bool:
        # Determine if cleanup is needed
        total_files = len(log_files)
        total_size_mb = sum(f.size_mb for f in log_files)
        
        # Check various conditions
        conditions = [
            total_files > self.config["max_files"],
            total_size_mb > self.config["max_total_size_mb"],
            any(f.age_hours > self.config["max_age_days"] * 24 for f in log_files),
            any(f.size_bytes < 100 for f in log_files)  # Very small/empty files
        ]
        
        return any(conditions)
    
    def perform_cleanup(self, dry_run: bool = False) -> Dict:
        # Perform intelligent log cleanup
        with self.lock:
            log_files = self.scan_log_files()
            
            if not log_files:
                return {"status": "no_files", "message": "No log files found"}
            
            if not self.should_cleanup(log_files):
                return {"status": "no_cleanup_needed", "files_count": len(log_files)}
            
            # Calculate priorities
            priorities = self.calculate_cleanup_priority(log_files)
            
            # Determine files to delete
            files_to_delete = []
            total_files = len(log_files)
            total_size_mb = sum(f.size_mb for f in log_files)
            
            for log_file, priority in priorities:
                # Safety checks
                if len(log_files) - len(files_to_delete) <= self.config["min_keep_files"]:
                    break  # Don't delete if we'd go below minimum
                
                if log_file.age_hours < self.config["keep_recent_hours"]:
                    continue  # Don't delete recent files
                
                # Decide to delete based on conditions
                should_delete = False
                
                # Always delete very old files
                if log_file.age_hours > self.config["max_age_days"] * 24:
                    should_delete = True
                
                # Delete if we have too many files
                elif total_files - len(files_to_delete) > self.config["max_files"]:
                    should_delete = True
                
                # Delete if total size is too large
                elif total_size_mb > self.config["max_total_size_mb"]:
                    should_delete = True
                    total_size_mb -= log_file.size_mb
                
                # Delete empty or very small files
                elif log_file.size_bytes < 1024:
                    should_delete = True
                
                if should_delete:
                    files_to_delete.append(log_file)
            
            # Execute deletion
            deleted_files = []
            bytes_freed = 0
            
            for log_file in files_to_delete:
                try:
                    if not dry_run:
                        log_file.path.unlink()
                    
                    deleted_files.append({
                        "name": log_file.path.name,
                        "size_kb": log_file.size_kb,
                        "age_hours": log_file.age_hours
                    })
                    bytes_freed += log_file.size_bytes
                    
                except OSError as e:
                    print(f"Error deleting {log_file.path}: {e}")
            
            # Update statistics
            if not dry_run:
                self.stats["files_deleted"] += len(deleted_files)
                self.stats["bytes_freed"] += bytes_freed
                self.stats["last_cleanup"] = datetime.now()
                self.stats["total_cleanups"] += 1
            
            return {
                "status": "success",
                "dry_run": dry_run,
                "files_before": total_files,
                "files_after": total_files - len(deleted_files),
                "deleted_files": deleted_files,
                "bytes_freed": bytes_freed,
                "mb_freed": bytes_freed / (1024 * 1024)
            }
    
    def auto_cleanup_if_needed(self) -> Dict:
        # Automatic cleanup with interval checking
        if self.stats["last_cleanup"]:
            hours_since_last = (datetime.now() - self.stats["last_cleanup"]).total_seconds() / 3600
            if hours_since_last < self.config["cleanup_interval_hours"]:
                return {"status": "too_soon", "hours_since_last": hours_since_last}
        
        return self.perform_cleanup(dry_run=False)
    
    def get_status(self) -> Dict:
        # Get current status and statistics
        log_files = self.scan_log_files()
        total_size_mb = sum(f.size_mb for f in log_files)
        
        return {
            "strategy": self.strategy.value,
            "config": self.config,
            "current_files": len(log_files),
            "current_size_mb": round(total_size_mb, 2),
            "needs_cleanup": self.should_cleanup(log_files),
            "stats": self.stats.copy()
        }
    
    def preview_cleanup(self) -> Dict:
        # Preview what would be deleted without actually deleting
        return self.perform_cleanup(dry_run=True)

# Global cleaner instance
_cleaner_instance = None

def get_log_cleaner(strategy: CleanupStrategy = CleanupStrategy.BALANCED) -> SmartLogCleaner:
    # Get global log cleaner instance
    global _cleaner_instance
    if _cleaner_instance is None:
        _cleaner_instance = SmartLogCleaner(strategy=strategy)
    return _cleaner_instance

def cleanup_logs_now(strategy: CleanupStrategy = CleanupStrategy.BALANCED, dry_run: bool = False) -> Dict:
    # Immediate log cleanup
    cleaner = get_log_cleaner(strategy)
    return cleaner.perform_cleanup(dry_run=dry_run)

def auto_cleanup_logs(strategy: CleanupStrategy = CleanupStrategy.BALANCED) -> Dict:
    # Automatic log cleanup with interval checking
    cleaner = get_log_cleaner(strategy)
    return cleaner.auto_cleanup_if_needed()

# Convenience functions for different strategies
def cleanup_conservative(dry_run: bool = False) -> Dict:
    return cleanup_logs_now(CleanupStrategy.CONSERVATIVE, dry_run)

def cleanup_balanced(dry_run: bool = False) -> Dict:
    return cleanup_logs_now(CleanupStrategy.BALANCED, dry_run)

def cleanup_aggressive(dry_run: bool = False) -> Dict:
    return cleanup_logs_now(CleanupStrategy.AGGRESSIVE, dry_run)

if __name__ == "__main__":
    # Command line interface for testing
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            cleaner = get_log_cleaner()
            status = cleaner.get_status()
            print(f"Current files: {status['current_files']}")
            print(f"Current size: {status['current_size_mb']} MB")
            print(f"Needs cleanup: {status['needs_cleanup']}")
            print(f"Strategy: {status['strategy']}")
            
        elif command == "preview":
            strategy_name = sys.argv[2] if len(sys.argv) > 2 else "balanced"
            strategy = CleanupStrategy(strategy_name)
            result = cleanup_logs_now(strategy, dry_run=True)
            print(f"Preview cleanup ({strategy_name}):")
            print(f"Would delete {len(result.get('deleted_files', []))} files")
            print(f"Would free {result.get('mb_freed', 0):.2f} MB")
            
        elif command == "clean":
            strategy_name = sys.argv[2] if len(sys.argv) > 2 else "balanced"
            strategy = CleanupStrategy(strategy_name)
            result = cleanup_logs_now(strategy, dry_run=False)
            print(f"Cleanup completed ({strategy_name}):")
            print(f"Deleted {len(result.get('deleted_files', []))} files")
            print(f"Freed {result.get('mb_freed', 0):.2f} MB")
            
        else:
            print("Usage: python auto_clean.py [status|preview|clean] [conservative|balanced|aggressive]")
    else:
        # Default: show status
        cleaner = get_log_cleaner()
        status = cleaner.get_status()
        print(f"ZSnapr Log Cleaner Status:")
        print(f"Files: {status['current_files']}, Size: {status['current_size_mb']} MB")
        print(f"Needs cleanup: {status['needs_cleanup']}")