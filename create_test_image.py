import matplotlib.pyplot as plt
import numpy as np

def create_test_chart():
    # Create data
    x = np.logspace(-1, 5, 100) # 0.1 to 100k
    y = 100 / x # Inverse relationship
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot thick blue line (mimicking the band)
    ax.loglog(x, y, color='blue', linewidth=10, solid_capstyle='round')
    
    # Grid
    ax.grid(True, which="both", ls="-", alpha=0.5)
    
    # Limits
    ax.set_xlim(0.1, 100000)
    ax.set_ylim(0.01, 1000)
    
    # Save
    plt.savefig('test_chart.png', dpi=100)
    print("Created test_chart.png")

if __name__ == "__main__":
    create_test_chart()
