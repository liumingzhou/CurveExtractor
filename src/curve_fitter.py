import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from scipy.optimize import curve_fit
from scipy.stats import t

# Try to set Chinese font
try:
    import platform
    if platform.system() == "Windows":
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
    elif platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Heiti TC', 'Arial']
    else:
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Droid Sans Fallback', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

class CurveFitter:
    def __init__(self):
        pass

    def fit_data(self, x, y, model_type, order=1, confidence=0.95):
        """
        Fits data to the specified model.
        Returns a dictionary with results.
        """
        x = np.array(x)
        y = np.array(y)
        
        # Sort data by x for better plotting
        sort_idx = np.argsort(x)
        x = x[sort_idx]
        y = y[sort_idx]

        results = {
            'x': x,
            'y_true': y,
            'model_type': model_type,
            'equation': '',
            'params': [],
            'y_pred': None,
            'r_squared': 0,
            'residuals': None,
            'confidence_interval': None
        }

        try:
            if model_type == 'Linear':
                popt, pcov = curve_fit(self._linear, x, y)
                results['y_pred'] = self._linear(x, *popt)
                results['equation'] = f"y = {popt[0]:.4e} * x + {popt[1]:.4e}"
                results['params'] = popt
            
            elif model_type == 'Polynomial':
                popt = np.polyfit(x, y, order)
                results['y_pred'] = np.polyval(popt, x)
                eq_parts = []
                for i, c in enumerate(popt):
                    power = order - i
                    eq_parts.append(f"{c:.4e} * x^{power}")
                results['equation'] = "y = " + " + ".join(eq_parts).replace("x^0", "").replace("x^1 ", "x ")
                results['params'] = popt

            elif model_type == 'Exponential':
                # y = a * exp(b * x)
                # Linearize: ln(y) = ln(a) + b * x
                # Only works for y > 0
                valid_mask = y > 0
                if np.sum(valid_mask) < 2:
                    raise ValueError("Data must be positive for Exponential fit")
                
                log_y = np.log(y[valid_mask])
                x_valid = x[valid_mask]
                
                popt = np.polyfit(x_valid, log_y, 1)
                b = popt[0]
                a = np.exp(popt[1])
                
                results['y_pred'] = a * np.exp(b * x)
                results['equation'] = f"y = {a:.4e} * e^({b:.4e} * x)"
                results['params'] = [a, b]

            elif model_type == 'Logarithmic':
                # y = a + b * ln(x)
                # Only works for x > 0
                valid_mask = x > 0
                if np.sum(valid_mask) < 2:
                    raise ValueError("X must be positive for Logarithmic fit")
                
                log_x = np.log(x[valid_mask])
                y_valid = y[valid_mask]
                
                popt = np.polyfit(log_x, y_valid, 1)
                b = popt[0]
                a = popt[1]
                
                results['y_pred'] = a + b * np.log(x)
                results['equation'] = f"y = {a:.4e} + {b:.4e} * ln(x)"
                results['params'] = [a, b]
                
            elif model_type == 'Power':
                # y = a * x^b
                # ln(y) = ln(a) + b * ln(x)
                valid_mask = (x > 0) & (y > 0)
                if np.sum(valid_mask) < 2:
                     raise ValueError("X and Y must be positive for Power fit")
                
                log_x = np.log(x[valid_mask])
                log_y = np.log(y[valid_mask])
                
                popt = np.polyfit(log_x, log_y, 1)
                b = popt[0]
                a = np.exp(popt[1])
                
                results['y_pred'] = a * np.power(x, b)
                results['equation'] = f"y = {a:.4e} * x^({b:.4e})"
                results['params'] = [a, b]

            else:
                raise ValueError(f"Unknown model type: {model_type}")

            # Calculate Statistics
            residuals = y - results['y_pred']
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r_squared = 1 - (ss_res / ss_tot)
            
            results['residuals'] = residuals
            results['r_squared'] = r_squared
            
            # Calculate Confidence Interval (Simplified for mean response)
            # This is a bit complex for general non-linear, using standard error approximation
            n = len(x)
            p = len(results['params']) # Number of parameters
            dof = max(1, n - p)
            
            # Standard error of regression
            s_err = np.sqrt(ss_res / dof)
            
            # t-value
            t_val = t.ppf((1 + confidence) / 2, dof)
            
            # Margin of error (approximate, assuming uniform leverage for simplicity in this quick implementation)
            # For rigorous CI, we need the Jacobian matrix.
            # Here we provide a basic prediction interval approximation width
            results['confidence_interval_width'] = t_val * s_err 

        except Exception as e:
            results['error'] = str(e)

        return results

    def _linear(self, x, a, b):
        return a * x + b

    def plot_fit(self, results, output_path=None, title="Curve Fitting Result"):
        """
        Generates a plot of the fit.
        """
        if 'error' in results:
            print(f"Cannot plot due to error: {results['error']}")
            return

        x = results['x']
        y = results['y_true']
        y_pred = results['y_pred']
        
        plt.figure(figsize=(10, 6), dpi=300)
        
        # Plot data points
        plt.scatter(x, y, color='blue', label='Original Data', alpha=0.6, s=20)
        
        # Plot fitted curve
        plt.plot(x, y_pred, color='red', label=f"Fit: {results['model_type']}", linewidth=2)
        
        # Add Confidence Interval (Visual approximation)
        if 'confidence_interval_width' in results:
            ci = results['confidence_interval_width']
            plt.fill_between(x, y_pred - ci, y_pred + ci, color='red', alpha=0.2, label='Confidence Interval')
        
        plt.title(f"{title}\n{results['equation']}\n$R^2 = {results['r_squared']:.4f}$")
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.5)
        
        # Check if log scale is better (heuristic)
        if np.max(x) / (np.min(x) + 1e-9) > 100:
            plt.xscale('log')
        if np.max(y) / (np.min(y) + 1e-9) > 100:
            plt.yscale('log')

        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300)
            print(f"Saved plot to {output_path}")
        
        # Close plot to free memory
        plt.close()
