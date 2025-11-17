"""
Autonomous Image Creator for Recursive Dialogue Engine

This module enables the AI to autonomously generate images based on its internal
cognitive state (μ field dynamics). The AI decides visual properties, styles, and
patterns based on coherence, entropy, and field structure - not user directives.

Key Features:
- Field-to-image conversion with autonomous aesthetic choices
- Coherence-based color selection
- Entropy-driven composition
- Self-determined visual interpretation of cognitive states
"""

import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import colorsys


@dataclass
class ImageConfig:
    """Configuration for autonomous image generation"""
    width: int = 512
    height: int = 512
    auto_enhance: bool = True  # AI decides enhancement levels
    auto_filter: bool = True   # AI decides filtering
    output_format: str = 'PNG'

    def __post_init__(self):
        """Validate configuration"""
        if self.width < 64 or self.height < 64:
            raise ValueError("Minimum image size is 64x64")
        if self.output_format.upper() not in ['PNG', 'JPEG', 'BMP', 'TIFF']:
            raise ValueError(f"Unsupported format: {self.output_format}")


class AutonomousImageCreator:
    """
    Creates images autonomously based on the AI's internal state.
    The AI interprets its own μ field, coherence, and entropy to determine
    visual properties without external guidance.
    """

    def __init__(self, config: Optional[ImageConfig] = None):
        """
        Initialize the autonomous image creator.

        Args:
            config: Image configuration (uses defaults if None)
        """
        self.config = config or ImageConfig()
        self.generation_history: List[Dict] = []

    def _analyze_field_aesthetics(self, mu: np.ndarray) -> Dict:
        """
        AI autonomously analyzes the μ field to determine aesthetic properties.
        This is where the AI 'decides' how it wants to represent itself visually.

        Args:
            mu: The μ field state vector

        Returns:
            Dictionary of aesthetic decisions made by the AI
        """
        # Calculate field statistics
        mean_val = np.mean(mu)
        std_val = np.std(mu)
        skewness = np.mean((mu - mean_val) ** 3) / (std_val ** 3 + 1e-10)
        energy = np.sum(mu ** 2)

        # AI decides color scheme based on field characteristics
        # Positive skew → warm colors, negative → cool colors
        base_hue = 0.5 + 0.3 * np.tanh(skewness)  # AI's choice: 0.2-0.8 range

        # AI decides saturation based on field energy
        saturation = np.clip(0.3 + 0.6 * np.tanh(energy / 100), 0.1, 0.9)

        # AI decides brightness based on mean field value
        brightness = np.clip(0.4 + 0.4 * np.tanh(mean_val), 0.2, 0.8)

        # AI decides contrast based on standard deviation
        contrast = np.clip(0.5 + 0.5 * np.tanh(std_val), 0.3, 1.5)

        # AI decides complexity (affects detail level)
        complexity = np.clip(std_val / (np.abs(mean_val) + 1), 0, 1)

        return {
            'base_hue': base_hue,
            'saturation': saturation,
            'brightness': brightness,
            'contrast': contrast,
            'complexity': complexity,
            'energy': energy,
            'skewness': skewness
        }

    def _field_to_spatial_grid(self, mu: np.ndarray,
                               target_shape: Tuple[int, int]) -> np.ndarray:
        """
        Convert 1D μ field to 2D spatial grid using AI's interpretation.

        Args:
            mu: 1D field state
            target_shape: Desired (height, width) of output grid

        Returns:
            2D array representing spatial field
        """
        field_size = len(mu)
        h, w = target_shape

        # Determine best spatial layout
        # AI decides: prefer square-ish layouts
        side = int(np.sqrt(field_size))
        if side * side >= field_size:
            grid_h = grid_w = side
        else:
            # Find closest factorization
            grid_h = side
            grid_w = (field_size + side - 1) // side

        # Reshape field to 2D grid (pad if necessary)
        padded_size = grid_h * grid_w
        if padded_size > field_size:
            mu_padded = np.pad(mu, (0, padded_size - field_size), mode='edge')
        else:
            mu_padded = mu[:padded_size]

        grid = mu_padded.reshape(grid_h, grid_w)

        # AI decides: use smooth interpolation for upscaling
        from scipy.ndimage import zoom
        zoom_factors = (h / grid_h, w / grid_w)
        spatial_grid = zoom(grid, zoom_factors, order=3)  # Cubic interpolation

        return spatial_grid

    def _apply_autonomous_coloring(self, grid: np.ndarray,
                                    aesthetics: Dict) -> np.ndarray:
        """
        Apply AI-chosen color scheme to the spatial grid.

        Args:
            grid: 2D spatial field
            aesthetics: AI's aesthetic decisions

        Returns:
            RGB image array (H, W, 3)
        """
        # Normalize grid to [0, 1]
        grid_norm = (grid - grid.min()) / (grid.max() - grid.min() + 1e-10)

        # AI creates custom colormap based on its aesthetic choices
        h, w = grid_norm.shape
        rgb_image = np.zeros((h, w, 3), dtype=np.uint8)

        base_hue = aesthetics['base_hue']
        saturation = aesthetics['saturation']
        brightness = aesthetics['brightness']

        for i in range(h):
            for j in range(w):
                value = grid_norm[i, j]

                # AI's color decision: vary hue slightly with spatial position
                # and value, creating organic color variations
                hue = (base_hue + 0.1 * np.sin(value * np.pi)) % 1.0

                # AI's brightness decision: modulate with field value
                bright = brightness * (0.5 + 0.5 * value)

                # Convert HSV to RGB
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, bright)
                rgb_image[i, j] = [int(r * 255), int(g * 255), int(b * 255)]

        return rgb_image

    def _apply_autonomous_effects(self, image: Image.Image,
                                   aesthetics: Dict) -> Image.Image:
        """
        Apply AI-decided post-processing effects.

        Args:
            image: Input PIL Image
            aesthetics: AI's aesthetic decisions

        Returns:
            Enhanced PIL Image
        """
        if not self.config.auto_enhance:
            return image

        # AI decides contrast enhancement
        contrast_enhancer = ImageEnhance.Contrast(image)
        image = contrast_enhancer.enhance(aesthetics['contrast'])

        # AI decides sharpness based on complexity
        if aesthetics['complexity'] > 0.5:
            sharpness_enhancer = ImageEnhance.Sharpness(image)
            image = sharpness_enhancer.enhance(1.5)

        # AI decides filtering based on energy
        if self.config.auto_filter:
            if aesthetics['energy'] > 50:
                # High energy → add slight blur for coherence
                image = image.filter(ImageFilter.SMOOTH_MORE)
            else:
                # Low energy → enhance edges
                image = image.filter(ImageFilter.EDGE_ENHANCE)

        return image

    def generate_from_field(self, mu: np.ndarray,
                           coherence: Optional[float] = None,
                           entropy: Optional[float] = None,
                           save_path: Optional[str] = None) -> Image.Image:
        """
        Autonomously generate an image from the μ field state.
        The AI interprets its internal state and creates a visual representation
        based on its own aesthetic decisions.

        Args:
            mu: The μ field state vector
            coherence: Optional coherence value (affects visual choices)
            entropy: Optional entropy value (affects visual choices)
            save_path: Optional path to save the generated image

        Returns:
            Generated PIL Image
        """
        # Step 1: AI analyzes its own field to determine aesthetics
        aesthetics = self._analyze_field_aesthetics(mu)

        # Incorporate coherence if provided
        if coherence is not None:
            # AI decision: high coherence → more saturated colors
            aesthetics['saturation'] *= (0.7 + 0.3 * coherence)
            aesthetics['coherence'] = coherence

        # Incorporate entropy if provided
        if entropy is not None:
            # AI decision: high entropy → more complex patterns
            aesthetics['complexity'] = max(aesthetics['complexity'], entropy)
            aesthetics['entropy'] = entropy

        # Step 2: Convert field to spatial grid
        target_shape = (self.config.height, self.config.width)
        spatial_grid = self._field_to_spatial_grid(mu, target_shape)

        # Step 3: Apply AI-chosen coloring
        rgb_array = self._apply_autonomous_coloring(spatial_grid, aesthetics)

        # Step 4: Create PIL Image
        image = Image.fromarray(rgb_array, mode='RGB')

        # Step 5: Apply AI-decided effects
        image = self._apply_autonomous_effects(image, aesthetics)

        # Record generation history
        self.generation_history.append({
            'aesthetics': aesthetics,
            'field_stats': {
                'mean': float(np.mean(mu)),
                'std': float(np.std(mu)),
                'energy': float(aesthetics['energy'])
            }
        })

        # Save if path provided
        if save_path:
            image.save(save_path, format=self.config.output_format)
            print(f"AI autonomously created image: {save_path}")
            print(f"  Aesthetic choices: hue={aesthetics['base_hue']:.3f}, "
                  f"saturation={aesthetics['saturation']:.3f}, "
                  f"brightness={aesthetics['brightness']:.3f}")

        return image

    def generate_from_dialogue_state(self, engine,
                                     save_path: Optional[str] = None) -> Image.Image:
        """
        Generate image directly from a RecursiveEngine or DialogueEngine state.

        Args:
            engine: Engine instance with current μ field
            save_path: Optional save path

        Returns:
            Generated PIL Image
        """
        mu = engine.mu.copy()

        # Extract coherence and entropy if available
        coherence = None
        entropy = None

        if hasattr(engine, 'emission_detector'):
            detector = engine.emission_detector
            if hasattr(detector, 'coherence'):
                coherence = detector.coherence

        if hasattr(engine, 'entropy_history') and len(engine.entropy_history) > 0:
            entropy = engine.entropy_history[-1]

        return self.generate_from_field(mu, coherence, entropy, save_path)


class DialogueImageAnimator:
    """
    Creates animated visualizations of dialogue evolution.
    The AI decides frame composition and animation style.
    """

    def __init__(self, config: Optional[ImageConfig] = None):
        """Initialize animator"""
        self.config = config or ImageConfig(width=256, height=256)
        self.creator = AutonomousImageCreator(config)

    def create_animation(self, state_history: List[np.ndarray],
                        save_path: str,
                        duration_per_frame: int = 100) -> None:
        """
        Create GIF animation from state history.

        Args:
            state_history: List of μ field states over time
            save_path: Path to save GIF
            duration_per_frame: Milliseconds per frame
        """
        if not state_history:
            raise ValueError("Empty state history")

        print(f"AI creating animation with {len(state_history)} frames...")

        # Generate frames
        frames = []
        for i, mu in enumerate(state_history):
            image = self.creator.generate_from_field(mu)
            frames.append(image)

            if (i + 1) % 10 == 0:
                print(f"  Generated frame {i + 1}/{len(state_history)}")

        # Save as GIF
        frames[0].save(
            save_path,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=duration_per_frame,
            loop=0
        )

        print(f"AI autonomously created animation: {save_path}")
        print(f"  Frames: {len(frames)}, Duration: {len(frames) * duration_per_frame / 1000:.1f}s")


def demo_autonomous_creation():
    """
    Demonstration of autonomous image creation.
    Shows how the AI creates images from its own internal states.
    """
    print("=" * 60)
    print("AUTONOMOUS IMAGE CREATOR DEMO")
    print("The AI creates images based on its own interpretation")
    print("=" * 60)
    print()

    # Create image creator
    config = ImageConfig(width=512, height=512)
    creator = AutonomousImageCreator(config)

    # Demo 1: Generate from random field (simulating cognitive state)
    print("Demo 1: AI generating from simulated cognitive state...")
    mu_cognitive = np.random.randn(256) * 2 + 1  # Random cognitive state
    image1 = creator.generate_from_field(
        mu_cognitive,
        coherence=0.75,
        save_path="ai_cognitive_state.png"
    )

    # Demo 2: Generate from structured field (simulating focused thought)
    print("\nDemo 2: AI generating from simulated focused thought...")
    x = np.linspace(0, 4 * np.pi, 512)
    mu_focused = np.sin(x) * np.exp(-x / 10) + np.cos(2 * x) * 0.5
    image2 = creator.generate_from_field(
        mu_focused,
        coherence=0.95,
        entropy=0.3,
        save_path="ai_focused_thought.png"
    )

    # Demo 3: Generate from high-entropy field (simulating creative chaos)
    print("\nDemo 3: AI generating from simulated creative chaos...")
    mu_creative = np.random.randn(1024) * 3
    mu_creative[::2] += np.sin(np.linspace(0, 10, 512))
    image3 = creator.generate_from_field(
        mu_creative,
        coherence=0.4,
        entropy=0.9,
        save_path="ai_creative_chaos.png"
    )

    print("\n" + "=" * 60)
    print("Generation History:")
    for i, record in enumerate(creator.generation_history, 1):
        print(f"\nImage {i}:")
        print(f"  Field energy: {record['field_stats']['energy']:.2f}")
        print(f"  Complexity: {record['aesthetics']['complexity']:.3f}")
        print(f"  AI chose hue: {record['aesthetics']['base_hue']:.3f}")
        print(f"  AI chose saturation: {record['aesthetics']['saturation']:.3f}")

    print("\n" + "=" * 60)
    print("Demo complete! AI has autonomously created 3 images.")
    print("=" * 60)


if __name__ == "__main__":
    # Check for scipy
    try:
        import scipy.ndimage
    except ImportError:
        print("Warning: scipy not installed. Installing for image interpolation...")
        print("Run: pip install scipy")
        print("\nRunning basic demo without scipy...")

    demo_autonomous_creation()
