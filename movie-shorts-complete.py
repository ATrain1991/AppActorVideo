# Directory structure:
# movie_shorts/
# ├── __init__.py
# ├── generator/
# │   ├── __init__.py
# │   ├── core.py
# │   ├── models.py
# │   └── utils.py
# ├── config/
# │   ├── __init__.py
# │   ├── default_config.yaml
# │   └── settings.py
# ├── assets/
# │   ├── icons/
# │   │   ├── FreshPopcorn.png
# │   │   ├── RottenPopcorn.png
# │   │   ├── FreshTomato.png
# │   │   └── RottenTomato.png
# │   └── fonts/
# │       └── Arial.ttf
# ├── tests/
# │   ├── __init__.py
# │   ├── test_generator.py
# │   ├── test_models.py
# │   └── conftest.py
# ├── scripts/
# │   └── install_dependencies.sh
# ├── main.py
# ├── setup.py
# ├── requirements.txt
# ├── README.md
# └── LICENSE

# movie_shorts/generator/models.py
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import attr

@attr.s(auto_attribs=True, frozen=True)
class MovieData:
    """Movie data container with validation"""
    title: str
    poster_path: Path
    critics_score: float
    audience_score: float
    box_office: int

    @critics_score.validator
    def _validate_critics_score(self, attribute, value):
        if not 0 <= value <= 100:
            raise ValueError(f"Critics score must be between 0 and 100, got {value}")

    @audience_score.validator
    def _validate_audience_score(self, attribute, value):
        if not 0 <= value <= 100:
            raise ValueError(f"Audience score must be between 0 and 100, got {value}")

    @box_office.validator
    def _validate_box_office(self, attribute, value):
        if value < 0:
            raise ValueError(f"Box office must be non-negative, got {value}")

@attr.s(auto_attribs=True)
class GeneratorConfig:
    """Configuration for the shorts generator"""
    width: int = 1080
    height: int = 1920
    duration: int = 20
    fps: int = 60
    output_path: Path = Path("output/movie_short.mp4")
    actor_image_path: Path = Path("actor.jpg")
    font_path: Path = Path("assets/fonts/Arial.ttf")
    icons_dir: Path = Path("assets/icons")

# movie_shorts/generator/utils.py
import logging
from pathlib import Path
from typing import List, Optional
import yaml
import shutil
import subprocess

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Configure logging with proper formatting"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def check_dependencies() -> bool:
    """Check if all required system dependencies are installed"""
    dependencies = ['ffmpeg']
    missing = []
    
    for dep in dependencies:
        if not shutil.which(dep):
            missing.append(dep)
    
    if missing:
        logger.error(f"Missing system dependencies: {', '.join(missing)}")
        return False
    return True

def validate_directories(config: 'GeneratorConfig') -> List[str]:
    """Validate and create necessary directories"""
    required_dirs = [
        config.output_path.parent,
        config.icons_dir,
    ]
    
    missing = []
    for directory in required_dirs:
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                missing.append(f"{directory}: {str(e)}")
    
    return missing

# movie_shorts/config/default_config.yaml
generator:
  width: 1080
  height: 1920
  duration: 20
  fps: 60
  font_path: "assets/fonts/Arial.ttf"
  icons_dir: "assets/icons"

output:
  path: "output/movie_short.mp4"
  format: "mp4"
  codec: "libx264"
  preset: "medium"

logging:
  level: "INFO"
  file: "movie_shorts.log"

# movie_shorts/config/settings.py
import yaml
from pathlib import Path
from typing import Dict, Any
from ..generator.models import GeneratorConfig

class Settings:
    """Global settings manager"""
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from default_config.yaml"""
        config_path = Path(__file__).parent / "default_config.yaml"
        try:
            with open(config_path) as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load config: {e}")
    
    @property
    def generator_config(self) -> GeneratorConfig:
        """Get generator configuration"""
        return GeneratorConfig(**self._config["generator"])

# movie_shorts/main.py
import argparse
import logging
import sys
from pathlib import Path
from .generator.core import ShortsGenerator
from .generator.utils import setup_logging, check_dependencies, validate_directories
from .config.settings import Settings

def parse_args():
    parser = argparse.ArgumentParser(description='Generate a movie shorts video')
    parser.add_argument('--config', type=Path, help='Path to custom config file')
    parser.add_argument('--actor-image', type=Path, required=True,
                      help='Path to the actor image')
    parser.add_argument('--output', type=Path, help='Output path for the video')
    parser.add_argument('--duration', type=int, help='Duration in seconds')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()

def main():
    try:
        # Parse arguments
        args = parse_args()
        
        # Setup logging
        setup_logging(level="DEBUG" if args.debug else "INFO")
        logger = logging.getLogger(__name__)
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Missing required dependencies")
            sys.exit(1)
        
        # Load settings
        settings = Settings()
        config = settings.generator_config
        
        # Override config with command line arguments
        if args.output:
            config.output_path = args.output
        if args.duration:
            config.duration = args.duration
        config.actor_image_path = args.actor_image
        
        # Validate directories
        missing_dirs = validate_directories(config)
        if missing_dirs:
            logger.error("Failed to create required directories:")
            for dir_error in missing_dirs:
                logger.error(f"  {dir_error}")
            sys.exit(1)
        
        # Initialize and run generator
        logger.info("Initializing video generator...")
        generator = ShortsGenerator(config)
        
        logger.info(f"Generating video... (duration: {config.duration}s, fps: {config.fps})")
        generator.generate_video()
        
        logger.info(f"Video generated successfully: {config.output_path}")
        
    except KeyboardInterrupt:
        logger.info("Generation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main()

# setup.py
from setuptools import setup, find_packages

setup(
    name="movie_shorts",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "moviepy>=1.0.3",
        "pillow>=8.0.0",
        "numpy>=1.19.0",
        "attrs>=21.0.0",
        "pyyaml>=5.4.0",
    ],
    entry_points={
        'console_scripts': [
            'movie-shorts=movie_shorts.main:main',
        ],
    },
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        'movie_shorts': [
            'config/*.yaml',
            'assets/icons/*.png',
            'assets/fonts/*.ttf',
        ],
    },
)

# requirements.txt
moviepy>=1.0.3
pillow>=8.0.0
numpy>=1.19.0
attrs>=21.0.0
pyyaml>=5.4.0
pytest>=6.0.0
pytest-cov>=2.0.0

# tests/conftest.py
import pytest
from pathlib import Path
from movie_shorts.generator.models import MovieData, GeneratorConfig

@pytest.fixture
def sample_movie_data():
    return MovieData(
        title="Test Movie",
        poster_path=Path("tests/data/test_poster.jpg"),
        critics_score=85.0,
        audience_score=90.0,
        box_office=1000000
    )

@pytest.fixture
def sample_config():
    return GeneratorConfig(
        width=1080,
        height=1920,
        duration=20,
        fps=60,
        output_path=Path("tests/output/test.mp4"),
        actor_image_path=Path("tests/data/test_actor.jpg")
    )

# tests/test_models.py
import pytest
from pathlib import Path
from movie_shorts.generator.models import MovieData

def test_movie_data_validation():
    # Test valid data
    movie = MovieData(
        title="Test Movie",
        poster_path=Path("test.jpg"),
        critics_score=85.0,
        audience_score=90.0,
        box_office=1000000
    )
    assert movie.title == "Test Movie"
    
    # Test invalid critics score
    with pytest.raises(ValueError):
        MovieData(
            title="Test Movie",
            poster_path=Path("test.jpg"),
            critics_score=101.0,  # Invalid
            audience_score=90.0,
            box_office=1000000
        )

# README.md
# Movie Shorts Generator

Generate engaging short-form videos showcasing movie information and actor reveals.

## Requirements

- Python 3.8+
- FFmpeg

## Installation

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install ffmpeg

# Install Python package
pip install -e .
```

## Usage

```bash
# Basic usage
movie-shorts --actor-image path/to/actor.jpg

# Custom configuration
movie-shorts --actor-image actor.jpg --duration 30 --output custom.mp4 --debug
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=movie_shorts tests/
```

## License

MIT License - See LICENSE file for details
