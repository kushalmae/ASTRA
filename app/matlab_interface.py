import subprocess
import json
import os
import datetime
import random
from app.config import Config

class MatlabInterface:
    def __init__(self, config=None):
        """Initialize the MATLAB interface."""
        self.config = config or Config()
        self.matlab_path = self.config.get_matlab_scripts_path()
        self.use_simulation = os.getenv("USE_SIMULATION", "False").lower() in ("true", "1", "yes")
        os.makedirs(self.matlab_path, exist_ok=True)
        
    def run_script(self, script_name, payload_id=None):
        """Run a MATLAB script and return the result."""
        try:
            # Check if we should use simulation instead of real MATLAB
            if self.use_simulation:
                return self._simulate_matlab_output(script_name, payload_id)
                
            # Check if the MATLAB script exists
            use_real_matlab = os.path.exists(os.path.join(self.matlab_path, f"sample_{script_name}_monitor.m"))
            
            if use_real_matlab:
                try:
                    results = self._run_real_matlab_script(script_name, payload_id)
                    # If we got no results from the real script, fall back to simulation
                    if not results:
                        print(f"No results from real MATLAB script {script_name}, falling back to simulation")
                        return self._simulate_matlab_output(script_name, payload_id)
                    return results
                except Exception as e:
                    print(f"Error running real MATLAB script {script_name}: {e}")
                    print("Falling back to simulation")
                    return self._simulate_matlab_output(script_name, payload_id)
            else:
                return self._simulate_matlab_output(script_name, payload_id)
        except Exception as e:
            print(f"Error running MATLAB script: {e}")
            # Always fall back to simulation if there's an error
            try:
                return self._simulate_matlab_output(script_name, payload_id)
            except Exception as sim_error:
                print(f"Error in simulation fallback: {sim_error}")
                return []
    
    def _run_real_matlab_script(self, script_name, payload_id=None):
        """Execute a real MATLAB script using subprocess."""
        try:
            # Construct the MATLAB command
            matlab_exe = "matlab"  # Or provide the full path to matlab.exe
            script_file = os.path.join(self.matlab_path, f"sample_{script_name}_monitor.m")
            script_name = f"sample_{script_name}_monitor"
            
            # Use a more reliable approach for MATLAB execution
            # Create a temporary MATLAB command file
            command_file_content = f"cd('{os.path.abspath(self.matlab_path)}');\n"
            
            if payload_id:
                command_file_content += f"{script_name}({payload_id});\n"
            else:
                command_file_content += f"{script_name};\n"
                
            command_file_content += "exit;\n"
            
            # Write the command to a temporary file
            temp_command_file = os.path.join(self.matlab_path, "temp_command.m")
            with open(temp_command_file, 'w') as f:
                f.write(command_file_content)
            
            # Run MATLAB with the command file
            cmd = [matlab_exe, "-batch", f"run('{os.path.abspath(temp_command_file)}')"]
            
            # Run the MATLAB command and capture the output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Clean up the temporary file
            try:
                os.remove(temp_command_file)
            except:
                pass
            
            if stderr:
                print(f"MATLAB error: {stderr}")
            
            if process.returncode != 0:
                print(f"MATLAB process returned non-zero exit code: {process.returncode}")
                return []
            
            # Parse the JSON output from MATLAB
            # Find the JSON part in the output (MATLAB might include additional text)
            json_start = stdout.find("{")
            if json_start >= 0:
                json_str = stdout[json_start:]
                try:
                    data = json.loads(json_str)
                    return data.get("results", [])
                except json.JSONDecodeError as e:
                    print(f"Failed to parse MATLAB JSON output: {e}")
                    print(f"MATLAB output: {json_str}")
                    return []
            else:
                print(f"No JSON found in MATLAB output. Full output: {stdout}")
                return []
                
        except Exception as e:
            print(f"Error running real MATLAB script: {e}")
            return []
    
    def _simulate_matlab_output(self, script_name, payload_id=None):
        """Simulate a MATLAB script output for testing purposes."""
        # Get the available metrics and payloads from config
        metrics = list(self.config.get_metrics().keys())
        payloads = self.config.get_payloads()
        
        # If payload_id is provided, filter the payloads
        if payload_id:
            payloads = [p for p in payloads if p["scid"] == payload_id]
        
        # If no payloads match, return no results
        if not payloads:
            return []
        
        # Generate random results for each payload
        results = []
        for payload in payloads:
            scid = payload["scid"]
            
            # Select a random metric or use all metrics depending on script_name
            if script_name == "all_metrics":
                selected_metrics = metrics
            elif script_name in metrics:
                selected_metrics = [script_name]
            else:
                selected_metrics = [random.choice(metrics)]
            
            for metric in selected_metrics:
                # Get the threshold for this metric
                threshold = self.config.get_threshold(metric)
                
                # Generate a random value with a chance to exceed the threshold
                if metric == "thermal":
                    base = 70
                    variation = 10
                elif metric == "voltage":
                    base = 3.0
                    variation = 0.5
                elif metric == "latency":
                    base = 200
                    variation = 100
                else:
                    base = threshold * 0.8
                    variation = threshold * 0.4
                
                value = base + random.uniform(0, variation)
                
                # Determine status
                status = "BREACH" if value > threshold else "NORMAL"
                
                # Only return breaches in this simulation
                if status == "BREACH" or random.random() < 0.3:  # 30% chance to include normal readings
                    timestamp = datetime.datetime.now().isoformat()
                    results.append({
                        "timestamp": timestamp,
                        "scid": scid,
                        "metric_type": metric,
                        "value": value,
                        "threshold": threshold,
                        "status": status
                    })
        
        return results
    
    def monitor_all_metrics(self):
        """Monitor all metrics for all payloads."""
        results = []
        
        # If simulation mode is enabled, just use that
        if self.use_simulation:
            return self._simulate_matlab_output("all_metrics")
        
        # Check if we need to use real MATLAB scripts or simulated data
        use_real_matlab = any(os.path.exists(os.path.join(self.matlab_path, f"sample_{metric}_monitor.m")) 
                             for metric in self.config.get_metrics())
        
        if use_real_matlab:
            # Run each metric script individually and combine results
            for metric in self.config.get_metrics():
                try:
                    metric_results = self.run_script(metric)
                    results.extend(metric_results)
                except Exception as e:
                    print(f"Error monitoring metric {metric}: {e}")
        else:
            # Use simulated data
            results = self._simulate_matlab_output("all_metrics")
        
        return results
    
    def monitor_specific_metric(self, metric_name, payload_id=None):
        """Monitor a specific metric, optionally for a specific payload."""
        return self.run_script(metric_name, payload_id) 