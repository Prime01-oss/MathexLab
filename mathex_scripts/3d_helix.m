% 3D Conical Helix Animation
clf
figure
view(3)
grid on
axis([-20 20 -20 20 0 40])
title('Generating 3D Conical Helix')

% Create animated lines
h1 = animatedline('Color', 'r', 'LineWidth', 2);
h2 = animatedline('Color', 'b', 'LineWidth', 2);

% Loop
for t = 0:0.1:40
    % Helix 1
    x1 = t * cos(t);
    y1 = t * sin(t);
    z1 = t;
    
    % Helix 2 (Phase shifted)
    x2 = t * cos(t + pi);
    y2 = t * sin(t + pi);
    z2 = t;
    
    addpoints(h1, x1, y1, z1);
    addpoints(h2, x2, y2, z2);
    
    drawnow
end