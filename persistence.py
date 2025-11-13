"""
Idle Persistence Layer for Recursive Dialogue Engine

Provides:
- State serialization and deserialization
- Idle detection and auto-save
- Checkpoint management
- Resume capability

Enables saving/loading complete dialogue state between sessions
or during idle periods (gaps between emissions).
"""

import numpy as np
import json
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from collections import deque
import time

if TYPE_CHECKING:
    from dialogue_system import RecursiveDialogueEngine, DialogueConfig


class IdleMonitor:
    """
    Monitors dialogue engine for idle states and triggers persistence.

    An "idle" state is defined as:
    - No emissions for idle_threshold_steps
    - Time since last activity exceeds idle_timeout_seconds
    """

    def __init__(self,
                 idle_threshold_steps: int = 100,
                 idle_timeout_seconds: float = 30.0,
                 auto_save: bool = True):
        """
        Args:
            idle_threshold_steps: Steps without emission to consider idle
            idle_timeout_seconds: Wall-clock time to consider idle
            auto_save: Automatically save state when idle detected
        """
        self.idle_threshold_steps = idle_threshold_steps
        self.idle_timeout_seconds = idle_timeout_seconds
        self.auto_save = auto_save

        # State tracking
        self.last_emission_step = 0
        self.last_activity_time = time.time()
        self.idle_callbacks = []

    def register_idle_callback(self, callback):
        """Register a callback to execute when idle detected"""
        self.idle_callbacks.append(callback)

    def update_activity(self, current_step: int, emission_occurred: bool = False):
        """Update activity tracking"""
        if emission_occurred:
            self.last_emission_step = current_step
        self.last_activity_time = time.time()

    def check_idle(self, current_step: int) -> bool:
        """
        Check if system is currently idle.

        Returns:
            True if idle conditions met
        """
        steps_since_emission = current_step - self.last_emission_step
        time_since_activity = time.time() - self.last_activity_time

        step_idle = steps_since_emission >= self.idle_threshold_steps
        time_idle = time_since_activity >= self.idle_timeout_seconds

        return step_idle or time_idle

    def on_idle(self, engine: 'RecursiveDialogueEngine'):
        """Execute callbacks when idle detected"""
        for callback in self.idle_callbacks:
            callback(engine)


class DialoguePersistence:
    """
    Handles saving and loading of RecursiveDialogueEngine state.

    Supports:
    - Complete state serialization (numpy arrays + metadata)
    - Compressed storage using npz format
    - Config preservation as JSON
    - Resume from saved checkpoints
    """

    def __init__(self, base_dir: str = './checkpoints'):
        """
        Args:
            base_dir: Directory to store checkpoint files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, parents=True)

    def save(self,
             engine: 'RecursiveDialogueEngine',
             name: Optional[str] = None,
             include_full_history: bool = True) -> Path:
        """
        Save complete engine state to disk.

        Args:
            engine: RecursiveDialogueEngine instance to save
            name: Checkpoint name (auto-generated if None)
            include_full_history: Save full emission history (can be large)

        Returns:
            Path to saved checkpoint file
        """
        if name is None:
            name = f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.base_dir / f"{name}.npz"

        # Extract state from engine
        state_dict = self._extract_state(engine, include_full_history)

        # Save config separately as JSON
        config_dict = self._serialize_config(engine.config)
        config_path = self.base_dir / f"{name}_config.json"
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        # Save arrays (compressed)
        np.savez_compressed(filepath, **state_dict)

        return filepath

    def load(self, name: str) -> 'RecursiveDialogueEngine':
        """
        Load engine state from disk and reconstruct engine.

        Args:
            name: Checkpoint name (without extension)

        Returns:
            Reconstructed RecursiveDialogueEngine with loaded state
        """
        filepath = self.base_dir / f"{name}.npz"
        config_path = self.base_dir / f"{name}_config.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Checkpoint not found: {filepath}")
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        # Load config
        with open(config_path, 'r') as f:
            config_dict = json.load(f)

        # Reconstruct config
        config = self._deserialize_config(config_dict)

        # Create new engine
        from dialogue_system import RecursiveDialogueEngine
        engine = RecursiveDialogueEngine(config)

        # Load and restore state
        data = np.load(filepath, allow_pickle=True)
        self._restore_state(engine, data)

        return engine

    def list_checkpoints(self) -> list:
        """List all available checkpoints"""
        checkpoints = []
        for npz_file in self.base_dir.glob("*.npz"):
            name = npz_file.stem
            config_file = self.base_dir / f"{name}_config.json"
            if config_file.exists():
                checkpoints.append({
                    'name': name,
                    'state_file': npz_file,
                    'config_file': config_file,
                    'size_mb': npz_file.stat().st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(npz_file.stat().st_mtime)
                })
        return sorted(checkpoints, key=lambda x: x['modified'], reverse=True)

    def delete_checkpoint(self, name: str):
        """Delete a checkpoint"""
        filepath = self.base_dir / f"{name}.npz"
        config_path = self.base_dir / f"{name}_config.json"

        if filepath.exists():
            filepath.unlink()
        if config_path.exists():
            config_path.unlink()

    def _extract_state(self,
                       engine: 'RecursiveDialogueEngine',
                       include_full_history: bool) -> Dict[str, Any]:
        """Extract all state from engine into numpy-saveable dict"""
        state_dict = {}

        # Core engine state
        state_dict['mu'] = self._to_numpy(engine.engine.mu)
        state_dict['mu_prev'] = self._to_numpy(engine.engine.mu_prev)
        state_dict['engine_t'] = np.array(engine.engine.t)

        # Detector state
        state_dict['entropy_history'] = np.array(list(engine.detector.entropy_history))
        state_dict['time_history'] = np.array(list(engine.detector.time_history))
        state_dict['steps_since_emission'] = np.array(engine.detector.steps_since_emission)
        state_dict['total_emissions'] = np.array(engine.detector.total_emissions)

        # PhaseCoherenceDetector has additional state
        if hasattr(engine.detector, 'last_emission_entropy'):
            val = engine.detector.last_emission_entropy
            state_dict['last_emission_entropy'] = np.array(val if val is not None else 0.0)

        # TDL state
        state_dict['last_token'] = np.array(
            engine.tdl.last_token if engine.tdl.last_token is not None else -1
        )
        state_dict['transition_matrix'] = engine.tdl.transition_matrix

        # LoMI state
        state_dict['mu_listener'] = engine.lomi.mu_listener
        state_dict['coherence_history'] = np.array(engine.lomi.coherence_history)

        # Codebook
        state_dict['codebook'] = engine.codebook

        # Global time
        state_dict['global_t'] = np.array(engine.t)

        # Emission history (can be large)
        if include_full_history and engine.emission_history:
            # Save emission metadata (not full mu_state arrays)
            state_dict['emission_tokens'] = np.array([e['token'] for e in engine.emission_history])
            state_dict['emission_times'] = np.array([e['time'] for e in engine.emission_history])
            state_dict['emission_coherences'] = np.array([e['coherence'] for e in engine.emission_history])

            # Save diagnostics as pickled object array
            state_dict['emission_diagnostics'] = np.array(
                [e['diagnostics'] for e in engine.emission_history],
                dtype=object
            )
        else:
            # Just save count
            state_dict['emission_count'] = np.array(len(engine.emission_history))

        return state_dict

    def _restore_state(self, engine: 'RecursiveDialogueEngine', data: np.lib.npyio.NpzFile):
        """Restore engine state from loaded numpy data"""
        # Core engine
        engine.engine.mu = self._from_numpy(data['mu'], engine.engine.mu)
        engine.engine.mu_prev = self._from_numpy(data['mu_prev'], engine.engine.mu_prev)
        engine.engine.t = int(data['engine_t'])

        # Detector
        entropy_hist = data['entropy_history'].tolist()
        time_hist = data['time_history'].tolist()

        engine.detector.entropy_history = deque(
            entropy_hist,
            maxlen=engine.detector.config.window_size
        )
        engine.detector.time_history = deque(
            time_hist,
            maxlen=engine.detector.config.window_size
        )
        engine.detector.steps_since_emission = int(data['steps_since_emission'])
        engine.detector.total_emissions = int(data['total_emissions'])

        if 'last_emission_entropy' in data and hasattr(engine.detector, 'last_emission_entropy'):
            val = float(data['last_emission_entropy'])
            engine.detector.last_emission_entropy = val if val != 0.0 else None

        # TDL
        last_token = int(data['last_token'])
        engine.tdl.last_token = last_token if last_token >= 0 else None
        engine.tdl.transition_matrix = data['transition_matrix'].copy()

        # LoMI
        engine.lomi.mu_listener = data['mu_listener'].copy()
        engine.lomi.coherence_history = data['coherence_history'].tolist()

        # Codebook
        engine.codebook = data['codebook'].copy()

        # Global time
        engine.t = int(data['global_t'])

        # Emission history (reconstructed)
        if 'emission_tokens' in data:
            engine.emission_history = []
            for i in range(len(data['emission_tokens'])):
                emission = {
                    'time': int(data['emission_times'][i]),
                    'token': int(data['emission_tokens'][i]),
                    'coherence': float(data['emission_coherences'][i]),
                    'mu_state': None,  # Not saved to conserve space
                    'diagnostics': data['emission_diagnostics'][i] if 'emission_diagnostics' in data else {}
                }
                engine.emission_history.append(emission)
        else:
            # History not saved, just clear it
            engine.emission_history = []

    def _serialize_config(self, config: 'DialogueConfig') -> Dict:
        """Convert DialogueConfig to JSON-serializable dict"""
        from recursive_engine import RecursiveParams
        from emission_detector import EmissionConfig

        config_dict = {
            'state_dims': config.state_dims,
            'vocab_size': config.vocab_size,
            'use_coherence_detector': config.use_coherence_detector,
            'feedback_decay': config.feedback_decay,
            'engine_optimization': config.engine_optimization,

            # Engine params
            'engine_params': {
                'g': config.engine_params.g,
                'lam': config.engine_params.lam,
                'rho': config.engine_params.rho,
                'eta': config.engine_params.eta,
                'dt': config.engine_params.dt,
                'dx': config.engine_params.dx if hasattr(config.engine_params, 'dx') else 1.0,
            },

            # Emission config
            'emission_config': {
                'entropy_threshold': config.emission_config.entropy_threshold,
                'window_size': config.emission_config.window_size,
                'cooldown_steps': config.emission_config.cooldown_steps,
                'energy_min': config.emission_config.energy_min,
                'energy_max': config.emission_config.energy_max,
            }
        }

        return config_dict

    def _deserialize_config(self, config_dict: Dict) -> 'DialogueConfig':
        """Reconstruct DialogueConfig from dict"""
        from dialogue_system import DialogueConfig
        from recursive_engine import RecursiveParams
        from emission_detector import EmissionConfig

        # Reconstruct nested configs
        engine_params = RecursiveParams(**config_dict['engine_params'])
        emission_config = EmissionConfig(**config_dict['emission_config'])

        # Create main config
        config = DialogueConfig(
            state_dims=config_dict['state_dims'],
            vocab_size=config_dict['vocab_size'],
            use_coherence_detector=config_dict['use_coherence_detector'],
            feedback_decay=config_dict['feedback_decay'],
            engine_optimization=config_dict['engine_optimization'],
            engine_params=engine_params,
            emission_config=emission_config
        )

        return config

    def _to_numpy(self, arr) -> np.ndarray:
        """Convert array to numpy (handles PyTorch tensors)"""
        if hasattr(arr, 'cpu'):  # PyTorch tensor
            return arr.cpu().numpy()
        return np.array(arr)

    def _from_numpy(self, arr: np.ndarray, reference):
        """Convert numpy array back to original type (numpy or PyTorch)"""
        if hasattr(reference, 'device'):  # PyTorch tensor
            try:
                import torch
                return torch.tensor(arr, device=reference.device, dtype=reference.dtype)
            except ImportError:
                # PyTorch not available, return numpy array
                print("Warning: PyTorch not available, returning numpy array")
                return arr.copy()
        return arr.copy()


def create_auto_save_callback(persistence: DialoguePersistence,
                               checkpoint_name: str = 'auto_idle') -> callable:
    """
    Create a callback for IdleMonitor that auto-saves on idle.

    Usage:
        monitor = IdleMonitor()
        persistence = DialoguePersistence()
        monitor.register_idle_callback(
            create_auto_save_callback(persistence, 'my_checkpoint')
        )
    """
    def callback(engine: 'RecursiveDialogueEngine'):
        filepath = persistence.save(engine, name=checkpoint_name)
        print(f"[Idle Auto-Save] State saved to {filepath}")

    return callback


if __name__ == "__main__":
    print("=== Idle Persistence Layer Demo ===\n")

    # This demo shows how to use the persistence system
    from dialogue_system import RecursiveDialogueEngine, DialogueConfig

    # Create engine
    config = DialogueConfig(state_dims=128, vocab_size=50, engine_optimization='fft')
    engine = RecursiveDialogueEngine(config)

    # Run for a bit
    print("Running dialogue for 200 steps...")
    emissions = engine.converse(n_steps=200, verbose=False)
    print(f"Generated {len(emissions)} emissions")

    # Save state
    persistence = DialoguePersistence('./demo_checkpoints')
    save_path = persistence.save(engine, name='demo_state')
    print(f"\nSaved state to: {save_path}")

    # List checkpoints
    print("\nAvailable checkpoints:")
    for cp in persistence.list_checkpoints():
        print(f"  - {cp['name']} ({cp['size_mb']:.2f} MB) - {cp['modified']}")

    # Continue running original engine
    print("\nContinuing original engine for 200 more steps...")
    more_emissions = engine.converse(n_steps=200, verbose=False)
    print(f"Total emissions now: {len(engine.emission_history)}")

    # Load saved state
    print("\nLoading saved state...")
    engine2 = persistence.load('demo_state')
    print(f"Loaded engine has {len(engine2.emission_history)} emissions")
    print(f"Loaded engine at time step: {engine2.t}")

    # Resume from loaded state
    print("\nResuming from loaded state for 200 steps...")
    resumed_emissions = engine2.converse(n_steps=200, verbose=False)
    print(f"After resume: {len(engine2.emission_history)} total emissions")

    print("\n=== Demo Complete ===")
    print("The persistence system successfully saved and restored engine state!")
