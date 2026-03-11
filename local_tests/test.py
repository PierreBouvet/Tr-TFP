import numpy as np
import time

def benchmark_polyfit():
    print(f"{'N':>10} | {'Time (ms)':>12}")
    print("-" * 25)
    
    # Range of input sizes
    N_values = [10**i for i in range(2, 7)]
    degree = 2
    
    for n in N_values:
        x = np.linspace(0, 10, n)
        y = 3*x**2 + 2*x + 1 + np.random.normal(0, 0.1, n)
        
        # Warmup
        np.polyfit(x, y, degree)
        
        # Timing
        start = time.perf_counter()
        iters = 100 if n < 10**5 else 10
        for _ in range(iters):
            np.polyfit(x, y, degree)
        end = time.perf_counter()
        
        avg_time_ms = ((end - start) / iters) * 1000
        print(f"{n:10d} | {avg_time_ms:12.4f}")

if __name__ == "__main__":
    benchmark_polyfit()
