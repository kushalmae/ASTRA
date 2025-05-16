% sample_voltage_monitor.m
%
% Example MATLAB script to monitor voltage metrics for satellite payloads
% Returns JSON with voltage measurements for the specified payload

function sample_voltage_monitor(scid)
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
    
    % Threshold for voltage metric (in a real system this would be read from a config)
    voltage_threshold = 3.3;
    
    % Get current timestamp in ISO format
    timestamp = datestr(now, 'yyyy-mm-ddTHH:MM:SS');
    
    % Initialize results array
    results_array = {};
    
    % Generate results for each payload
    for i = 1:length(payloads)
        payload_id = payloads(i);
        
        % Simulate a voltage reading (normally around 3.0 but sometimes higher)
        base_voltage = 3.0;
        variance = rand() * 0.5;  % Random value between 0 and 0.5
        voltage_value = base_voltage + variance;
        
        % Determine status
        if voltage_value > voltage_threshold
            status = 'BREACH';
        else
            status = 'NORMAL';
        end
        
        % Only return breaches or some normal readings
        if strcmp(status, 'BREACH') || rand() < 0.3
            % Create a structure for this result
            result = struct('timestamp', timestamp, ...
                       'scid', payload_id, ...
                       'metric_type', 'voltage', ...
                       'value', voltage_value, ...
                       'threshold', voltage_threshold, ...
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