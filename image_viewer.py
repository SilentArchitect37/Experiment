"""
Image Viewer Utility for Recursive Dialogue Engine

Provides simple image viewing capabilities for PNG, JPG, and other common formats.
Supports both single image viewing and grid display of multiple images.
"""

import os
from pathlib import Path
from typing import List, Union, Optional
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def view_image(image_path: Union[str, Path], title: Optional[str] = None, figsize: tuple = (10, 8)):
    """
    Display a single image file.

    Parameters:
    -----------
    image_path : str or Path
        Path to the image file
    title : str, optional
        Title to display above the image
    figsize : tuple, default (10, 8)
        Figure size in inches (width, height)

    Supported formats:
    - PNG, JPG, JPEG, BMP, GIF, TIFF, and more

    Example:
    --------
    >>> view_image('field_evolution.png', title='Field Evolution')
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Use PIL if available for better format support
    if PIL_AVAILABLE:
        img = Image.open(image_path)
        plt.figure(figsize=figsize)
        plt.imshow(img)
        plt.axis('off')
        if title:
            plt.title(title, fontsize=14, pad=10)
        elif not title:
            plt.title(image_path.name, fontsize=12, pad=10)
        plt.tight_layout()
        plt.show()
    else:
        # Fallback to matplotlib's native image reading
        img = mpimg.imread(image_path)
        plt.figure(figsize=figsize)
        plt.imshow(img)
        plt.axis('off')
        if title:
            plt.title(title, fontsize=14, pad=10)
        elif not title:
            plt.title(image_path.name, fontsize=12, pad=10)
        plt.tight_layout()
        plt.show()


def view_images(image_paths: List[Union[str, Path]],
                titles: Optional[List[str]] = None,
                cols: int = 2,
                figsize: tuple = (15, 10)):
    """
    Display multiple images in a grid layout.

    Parameters:
    -----------
    image_paths : list of str or Path
        List of paths to image files
    titles : list of str, optional
        List of titles for each image (must match length of image_paths)
    cols : int, default 2
        Number of columns in the grid
    figsize : tuple, default (15, 10)
        Figure size in inches (width, height)

    Example:
    --------
    >>> view_images(['field_evolution.png', 'entropy_trajectory.png'],
    ...             titles=['Field Evolution', 'Entropy'])
    """
    image_paths = [Path(p) for p in image_paths]
    n_images = len(image_paths)

    if n_images == 0:
        raise ValueError("No images provided")

    # Check all files exist
    for img_path in image_paths:
        if not img_path.exists():
            raise FileNotFoundError(f"Image file not found: {img_path}")

    # Calculate grid dimensions
    rows = (n_images + cols - 1) // cols

    # Create figure and subplots
    fig, axes = plt.subplots(rows, cols, figsize=figsize)

    # Handle case of single row or column
    if rows == 1 and cols == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]
    elif cols == 1:
        axes = [[ax] for ax in axes]

    # Display images
    for idx, img_path in enumerate(image_paths):
        row = idx // cols
        col = idx % cols
        ax = axes[row][col] if rows > 1 else axes[col]

        # Load and display image
        if PIL_AVAILABLE:
            img = Image.open(img_path)
            ax.imshow(img)
        else:
            img = mpimg.imread(img_path)
            ax.imshow(img)

        ax.axis('off')

        # Set title
        if titles and idx < len(titles):
            ax.set_title(titles[idx], fontsize=11, pad=8)
        else:
            ax.set_title(img_path.name, fontsize=10, pad=8)

    # Hide unused subplots
    for idx in range(n_images, rows * cols):
        row = idx // cols
        col = idx % cols
        ax = axes[row][col] if rows > 1 else axes[col]
        ax.axis('off')

    plt.tight_layout()
    plt.show()


def view_all_images_in_directory(directory: Union[str, Path] = '.',
                                  pattern: str = '*.png',
                                  cols: int = 2,
                                  figsize: tuple = (15, 10)):
    """
    Display all images matching a pattern in a directory.

    Parameters:
    -----------
    directory : str or Path, default '.'
        Directory to search for images
    pattern : str, default '*.png'
        Glob pattern for image files (e.g., '*.png', '*.jpg', '*.{png,jpg}')
    cols : int, default 2
        Number of columns in the grid
    figsize : tuple, default (15, 10)
        Figure size in inches (width, height)

    Example:
    --------
    >>> view_all_images_in_directory('.', pattern='*.png')
    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Find all matching images
    image_paths = list(directory.glob(pattern))

    if not image_paths:
        print(f"No images found matching pattern '{pattern}' in {directory}")
        return

    # Sort by modification time (newest first) or name
    image_paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    print(f"Found {len(image_paths)} image(s) in {directory}")

    view_images(image_paths, cols=cols, figsize=figsize)


def main():
    """
    Command-line interface for image viewing.

    Usage examples:
    ---------------
    # View a single image
    python image_viewer.py field_evolution.png

    # View all PNG files in current directory
    python image_viewer.py --all

    # View all PNG files with custom pattern
    python image_viewer.py --all --pattern "*.jpg"
    """
    import argparse

    parser = argparse.ArgumentParser(description='View image files')
    parser.add_argument('image', nargs='?', help='Path to image file')
    parser.add_argument('--all', action='store_true', help='View all images in current directory')
    parser.add_argument('--pattern', default='*.png', help='Glob pattern for --all mode (default: *.png)')
    parser.add_argument('--cols', type=int, default=2, help='Number of columns for grid display (default: 2)')
    parser.add_argument('--dir', default='.', help='Directory to search (default: current directory)')

    args = parser.parse_args()

    if args.all:
        view_all_images_in_directory(args.dir, pattern=args.pattern, cols=args.cols)
    elif args.image:
        view_image(args.image)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
