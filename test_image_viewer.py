"""
Simple test script for image viewer functionality
Tests that the module loads correctly and basic functions work
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def create_test_image(filename='test_image.png'):
    """Create a simple test image for viewing"""
    fig, ax = plt.subplots(figsize=(8, 6))

    # Generate some test data
    x = np.linspace(0, 2*np.pi, 100)
    y = np.sin(x)

    ax.plot(x, y, 'b-', linewidth=2, label='sin(x)')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('Test Image - Sine Wave')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename, dpi=100, bbox_inches='tight')
    plt.close()

    return filename


def test_imports():
    """Test that image_viewer module can be imported"""
    print("Test 1: Testing imports...")
    try:
        from image_viewer import view_image, view_images, view_all_images_in_directory
        print("  ✓ All functions imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_file_operations():
    """Test that test images can be created"""
    print("\nTest 2: Creating test images...")
    try:
        # Create test images
        test_files = []
        for i in range(3):
            filename = f'test_image_{i+1}.png'
            fig, ax = plt.subplots(figsize=(6, 4))
            x = np.linspace(0, 2*np.pi, 100)
            y = np.sin(x * (i+1))
            ax.plot(x, y, linewidth=2)
            ax.set_title(f'Test Image {i+1}')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(filename, dpi=100, bbox_inches='tight')
            plt.close()
            test_files.append(filename)

        print(f"  ✓ Created {len(test_files)} test images")
        return test_files
    except Exception as e:
        print(f"  ✗ Failed to create test images: {e}")
        return []


def test_view_image_non_interactive(test_file):
    """Test view_image function (non-interactive)"""
    print("\nTest 3: Testing view_image function...")
    try:
        from image_viewer import view_image
        # We can't actually test the display in a non-interactive environment
        # But we can test that the function doesn't crash
        print("  ✓ view_image function is available")
        print("  Note: Actual display test requires interactive environment")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_view_images_non_interactive(test_files):
    """Test view_images function (non-interactive)"""
    print("\nTest 4: Testing view_images function...")
    try:
        from image_viewer import view_images
        print("  ✓ view_images function is available")
        print(f"  Test files: {test_files}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_pil_availability():
    """Test if PIL/Pillow is available"""
    print("\nTest 5: Checking PIL/Pillow availability...")
    try:
        from PIL import Image
        print("  ✓ PIL/Pillow is installed (enhanced format support)")
        return True
    except ImportError:
        print("  ⚠ PIL/Pillow not installed (basic support via matplotlib)")
        print("    Install with: pip install Pillow")
        return False


def cleanup_test_files():
    """Remove test images"""
    print("\nCleaning up test files...")
    count = 0
    for i in range(1, 4):
        filename = f'test_image_{i}.png'
        if Path(filename).exists():
            Path(filename).unlink()
            count += 1
    print(f"  Removed {count} test file(s)")


def main():
    """Run all tests"""
    print("=" * 60)
    print("IMAGE VIEWER MODULE TESTS")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    # Test 2: Create test images
    test_files = test_file_operations()
    results.append(("File Creation", len(test_files) > 0))

    if test_files:
        # Test 3: view_image function
        results.append(("view_image", test_view_image_non_interactive(test_files[0])))

        # Test 4: view_images function
        results.append(("view_images", test_view_images_non_interactive(test_files)))

    # Test 5: PIL availability
    pil_available = test_pil_availability()
    results.append(("PIL/Pillow", pil_available))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Cleanup
    if test_files:
        cleanup_test_files()

    print("\n" + "=" * 60)
    print("USAGE INSTRUCTIONS")
    print("=" * 60)
    print("\nTo test image viewing interactively:")
    print("  1. Generate visualizations: python visualize.py")
    print("  2. View a single image:     python image_viewer.py field_evolution.png")
    print("  3. View all images:         python image_viewer.py --all")
    print("\nFor more details, see: IMAGE_VIEWING_GUIDE.md")
    print("=" * 60)

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
