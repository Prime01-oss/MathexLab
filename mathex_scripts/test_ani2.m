% Initialize Figure
clf
figure
view(3)      % Set 3D view
grid on
title('Lorenz Attractor Real-Time 3D')
xlabel('X'); ylabel('Y'); zlabel('Z');

% Create a cyan 3D animated line
h = animatedline('Color', 'c', 'LineWidth', 1.5);

% Lorenz System Parameters
sigma = 10;
beta = 8/3;
rho = 28;
dt = 0.015;

% Initial State
x = 1;
y = 1;
z = 1;

% Animation Loop
for i = 1:1500
    % Calculate derivatives
    dx = sigma * (y - x) * dt;
    dy = (x * (rho - z) - y) * dt;
    dz = (x * y - beta * z) * dt;
    
    % Update state
    x = x + dx;
    y = y + dy;
    z = z + dz;
    
    % Add point to 3D line
    addpoints(h, x, y, z);
    
    % Force render
    drawnow
    
    % Optional: Rotate camera slightly for dramatic effect
    % view(30 + i/5, 20) 
end