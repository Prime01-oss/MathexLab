% Create a struct
data = struct('mass', 10, 'velocity', [1 0 0]);

% Add a new field dynamically (This was impossible before!)
data.acceleration = 9.8;

% Use it in math
force = data.mass * data.acceleration;

disp(data)
disp(force)