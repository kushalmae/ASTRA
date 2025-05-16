% sample_thermal_monitor.m
%
% Example MATLAB script to monitor thermal metrics for satellite payloads
% Returns JSON with thermal measurements for the specified payload

function sample_thermal_monitor(scid)
    % Default to all payloads if no specific one provided
    if nargin < 1
        scid = 0;  % 0 means all payloads
    end
    
    % In a real system, this would read from telemetry files or databases
    % For this example, we'll just generate some sample data
    
    % Define available payloads
    payloads = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110];
    
    % Filter to specific payload if requested
    if scid > 0
        if ismember(scid, payloads)
            payloads = scid;
        else
            % Payload not found, return empty result
            results = struct('results', []);
            jsonString = jsonencode(results);
            disp(jsonString);
            return;
        end
    end
    
    % Threshold for thermal metric (in a real system this would be read from a config)
    thermal_threshold = 75.0;
    
    % Get current timestamp in ISO format
    timestamp = datestr(now, 'yyyy-mm-ddTHH:MM:SS');
    
    % Initialize results array
    results_array = {};
    
    % Generate results for each payload
    for i = 1:length(payloads)
        payload_id = payloads(i);
        
        % Simulate a thermal reading (normally around 70 but sometimes higher)
        base_temp = 70;
        variance = rand() * 10;  % Random value between 0 and 10
        thermal_value = base_temp + variance;
        
        % Determine status
        if thermal_value > thermal_threshold
            status = 'BREACH';
        else
            status = 'NORMAL';
        end
        
        % Only return breaches or some normal readings
        if strcmp(status, 'BREACH') || rand() < 0.3
            % Create a structure for this result
            result = struct('timestamp', timestamp, ...
                       'scid', payload_id, ...
                       'metric_type', 'thermal', ...
                       'value', thermal_value, ...
                       'threshold', thermal_threshold, ...
                       'status', status);
            
            % Add to results array
            results_array{end+1} = result;
        end
    end
    
    % Create and return JSON
    results = struct('results', {results_array});
    jsonString = jsonencode(results);
    
    % Print to stdout (this will be captured by the Python subprocess)
    disp(jsonString);
end 