"""
Comprehensive benchmark of Recursive Dialogue Engine optimizations

Compares:
1. Different engine optimizations (naive, vectorized, FFT, GPU)
2. Memory usage
3. Scaling with dimension size
4. End-to-end dialogue performance
"""

import numpy as np
import time
import sys
from typing import Dict, List
from dataclasses import dataclass

from recursive_engine import (
    create_engine, RecursiveParams, benchmark_engine, TORCH_AVAILABLE
)
from dialogue_system import RecursiveDialogueEngine, DialogueConfig


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    time_elapsed: float
    steps_per_sec: float
    emissions: int
    memory_mb: float = 0.0


def get_memory_usage() -> float:
    """Get current process memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def benchmark_engines(n_dims: int = 512, n_steps: int = 1000) -> Dict[str, BenchmarkResult]:
    """Benchmark different engine optimizations"""

    params = RecursiveParams()
    results = {}

    print(f"=== Engine Benchmark (dims={n_dims}, steps={n_steps}) ===\n")

    optimizations = ['naive', 'vectorized', 'fft']
    if TORCH_AVAILABLE:
        optimizations.append('gpu')

    for opt in optimizations:
        print(f"Testing {opt:12s}... ", end='', flush=True)

        try:
            engine = create_engine(opt, params, n_dims)
            mem_before = get_memory_usage()

            # Warm-up
            for _ in range(10):
                engine.step()

            # Benchmark
            start = time.perf_counter()
            for _ in range(n_steps):
                engine.step()
            elapsed = time.perf_counter() - start

            mem_after = get_memory_usage()
            mem_used = max(0, mem_after - mem_before)

            steps_per_sec = n_steps / elapsed

            results[opt] = BenchmarkResult(
                name=opt,
                time_elapsed=elapsed,
                steps_per_sec=steps_per_sec,
                emissions=0,  # Not applicable for raw engine
                memory_mb=mem_used
            )

            print(f"{elapsed:.3f}s  ({steps_per_sec:.1f} steps/s)  [{mem_used:.1f} MB]")

        except Exception as e:
            print(f"FAILED: {e}")

    return results


def benchmark_scaling(base_dims: int = 128, max_dims: int = 2048, n_steps: int = 500):
    """Benchmark how performance scales with state dimension"""

    print(f"\n=== Scaling Benchmark (steps={n_steps}) ===\n")
    print(f"{'Dims':>8s} | {'FFT (s)':>10s} | {'Steps/s':>10s} | {'Speedup vs Naive':>18s}")
    print("-" * 60)

    params = RecursiveParams()

    dims_list = [base_dims * (2 ** i) for i in range(5) if base_dims * (2 ** i) <= max_dims]

    for dims in dims_list:
        # FFT engine
        fft_engine = create_engine('fft', params, dims)
        elapsed_fft, sps_fft = benchmark_engine(fft_engine, n_steps)

        # Naive engine (only for small dims)
        speedup_str = "N/A"
        if dims <= 512:
            naive_engine = create_engine('naive', params, dims)
            elapsed_naive, sps_naive = benchmark_engine(naive_engine, n_steps)
            speedup = sps_fft / sps_naive
            speedup_str = f"{speedup:.1f}x"

        print(f"{dims:8d} | {elapsed_fft:10.3f} | {sps_fft:10.1f} | {speedup_str:>18s}")


def benchmark_dialogue(n_steps: int = 1000, verbose: bool = False):
    """Benchmark end-to-end dialogue system"""

    print(f"\n=== Dialogue System Benchmark (steps={n_steps}) ===\n")

    configs = {
        'FFT (small)': DialogueConfig(
            state_dims=256,
            vocab_size=100,
            engine_optimization='fft'
        ),
        'FFT (large)': DialogueConfig(
            state_dims=1024,
            vocab_size=1000,
            engine_optimization='fft'
        ),
    }

    if TORCH_AVAILABLE:
        configs['GPU (large)'] = DialogueConfig(
            state_dims=1024,
            vocab_size=1000,
            engine_optimization='gpu'
        )

    results = {}

    for name, config in configs.items():
        print(f"Testing {name:15s}... ", end='', flush=True)

        try:
            engine = RecursiveDialogueEngine(config)
            mem_before = get_memory_usage()

            start = time.perf_counter()
            emissions = engine.converse(n_steps=n_steps, verbose=False)
            elapsed = time.perf_counter() - start

            mem_after = get_memory_usage()
            mem_used = max(0, mem_after - mem_before)

            steps_per_sec = n_steps / elapsed

            results[name] = BenchmarkResult(
                name=name,
                time_elapsed=elapsed,
                steps_per_sec=steps_per_sec,
                emissions=len(emissions),
                memory_mb=mem_used
            )

            emission_rate = len(emissions) / n_steps
            print(f"{elapsed:.2f}s  ({steps_per_sec:.1f} steps/s)  [{len(emissions)} emissions, {emission_rate:.3f} rate]")

        except Exception as e:
            print(f"FAILED: {e}")

    return results


def benchmark_computational_complexity():
    """
    Analyze computational complexity of key operations

    Theoretical complexity:
    - Naive Laplacian: O(n²) with loops, O(n) with vectorization
    - FFT Laplacian: O(n log n)
    - Cubic term: O(n)
    - Total per step: O(n log n) for FFT, O(n²) for naive
    """

    print("\n=== Computational Complexity Analysis ===\n")

    print("Operation          | Naive    | Vectorized | FFT       | GPU")
    print("-" * 70)
    print("Laplacian          | O(n²)    | O(n)       | O(n log n)| O(n log n)")
    print("Cubic term         | O(n)     | O(n)       | O(n)      | O(n)")
    print("Momentum           | O(n)     | O(n)       | O(n)      | O(n)")
    print("Total per step     | O(n²)    | O(n)       | O(n log n)| O(n log n)")
    print()
    print("Memory usage       | O(n)     | O(n)       | O(n)      | O(n) + GPU")
    print()
    print("Key optimizations:")
    print("1. FFT Laplacian: Reduces O(n²) → O(n log n) for diffusion")
    print("2. Vectorization: Eliminates Python loops overhead")
    print("3. GPU: Parallelizes all O(n) operations across cores")
    print("4. In-place ops: Reduces memory allocations")
    print()


def print_summary(results: Dict[str, BenchmarkResult]):
    """Print summary comparison"""

    if not results:
        return

    print("\n=== Summary ===\n")

    # Find baseline (naive or slowest)
    baseline_name = min(results.keys(), key=lambda k: results[k].steps_per_sec)
    baseline_speed = results[baseline_name].steps_per_sec

    print(f"{'Method':15s} | {'Time (s)':>10s} | {'Steps/s':>10s} | {'Speedup':>10s} | {'Memory (MB)':>12s}")
    print("-" * 75)

    for name, res in sorted(results.items(), key=lambda x: -x[1].steps_per_sec):
        speedup = res.steps_per_sec / baseline_speed
        mem_str = f"{res.memory_mb:.1f}" if res.memory_mb > 0 else "N/A"
        print(f"{name:15s} | {res.time_elapsed:10.3f} | {res.steps_per_sec:10.1f} | {speedup:10.1f}x | {mem_str:>12s}")


def run_all_benchmarks():
    """Run comprehensive benchmark suite"""

    print("=" * 70)
    print("RECURSIVE DIALOGUE ENGINE - COMPREHENSIVE BENCHMARK")
    print("=" * 70)
    print()

    # 1. Engine benchmarks
    engine_results = benchmark_engines(n_dims=512, n_steps=1000)
    print_summary(engine_results)

    # 2. Scaling benchmark
    benchmark_scaling(base_dims=128, max_dims=2048, n_steps=500)

    # 3. Dialogue system benchmark
    dialogue_results = benchmark_dialogue(n_steps=1000)

    # 4. Complexity analysis
    benchmark_computational_complexity()

    print("\n" + "=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_benchmarks()
