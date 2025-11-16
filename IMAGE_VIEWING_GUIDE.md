# Image Viewing Guide

The Recursive Dialogue Engine now supports viewing PNG and other image files directly!

## Quick Start

### 1. View Images from Visualization Demo

Run the visualization demo with automatic image display:

```bash
python visualize.py
```

The demo will:
- Generate 4 visualization plots
- Save them as PNG files
- Display all images in a 2x2 grid

To save without displaying:
```bash
python visualize.py --no-display
```

### 2. View Individual Images

View a single image:
```bash
python image_viewer.py field_evolution.png
```

### 3. View All Images in Directory

View all PNG files in the current directory:
```bash
python image_viewer.py --all
```

View all JPG files:
```bash
python image_viewer.py --all --pattern "*.jpg"
```

View all images in a specific directory:
```bash
python image_viewer.py --all --dir ./outputs --pattern "*.png"
```

### 4. Customize Grid Layout

Change number of columns:
```bash
python image_viewer.py --all --cols 3
```

## Programmatic Usage

### View a Single Image

```python
from image_viewer import view_image

# View with default settings
view_image('field_evolution.png')

# View with custom title and size
view_image('entropy_trajectory.png',
          title='Entropy Over Time',
          figsize=(12, 8))
```

### View Multiple Images

```python
from image_viewer import view_images

images = [
    'field_evolution.png',
    'entropy_trajectory.png',
    'coherence_analysis.png',
    'phase_space.png'
]

# Display in 2x2 grid
view_images(images, cols=2)

# Display with custom titles
titles = [
    'Field Evolution',
    'Entropy Trajectory',
    'Coherence Analysis',
    'Phase Space'
]
view_images(images, titles=titles, cols=2, figsize=(16, 12))
```

### View All Images in Directory

```python
from image_viewer import view_all_images_in_directory

# View all PNG files in current directory
view_all_images_in_directory()

# View all JPG files in specific directory
view_all_images_in_directory('./outputs', pattern='*.jpg')
```

## Supported Image Formats

- **PNG** - Portable Network Graphics
- **JPG/JPEG** - Joint Photographic Experts Group
- **BMP** - Bitmap
- **GIF** - Graphics Interchange Format
- **TIFF** - Tagged Image File Format
- And more formats supported by PIL/Pillow

## Installation

The image viewer requires matplotlib (already installed) and optionally Pillow for enhanced format support:

```bash
pip install -r requirements.txt
```

Or install Pillow separately:
```bash
pip install Pillow
```

## Integration with Visualization System

The `visualize.py` module now automatically displays generated plots:

```python
from visualize import demo_visualization

# Generate and display all visualizations
demo_visualization(display=True)  # Default behavior

# Generate without displaying
demo_visualization(display=False)
```

## Tips

1. **Close windows to continue**: When viewing images, close the window to proceed to the next image
2. **Grid layout**: Use `cols` parameter to control how many columns in the grid
3. **Custom sizing**: Adjust `figsize=(width, height)` for optimal viewing
4. **Batch viewing**: Use `view_all_images_in_directory()` to quickly review all generated plots

## Examples

### Generate and View Visualizations
```bash
# Generate visualizations and view them
python visualize.py

# Generate only (no viewing)
python visualize.py --no-display
```

### View Previously Generated Images
```bash
# View all PNG files
python image_viewer.py --all

# View specific image
python image_viewer.py coherence_analysis.png
```

### Custom Python Script
```python
from image_viewer import view_images

# After generating some plots
my_images = ['plot1.png', 'plot2.png', 'plot3.png']
view_images(my_images, cols=3, figsize=(18, 6))
```

## Troubleshooting

**Images don't display?**
- Make sure you have a display/GUI environment
- Check that matplotlib backend supports display
- Try `export MPLBACKEND=TkAgg` before running

**Module not found error?**
- Ensure `image_viewer.py` is in the same directory
- Or add the directory to your Python path

**Pillow not installed?**
- The viewer works without Pillow using matplotlib
- For best format support, install: `pip install Pillow`
