% 3D Dynamic Surface Animation: Traveling Wave
clf
figure

% 1. Create Grid
[X, Y] = meshgrid(-8:0.4:8);
R = sqrt(X.^2 + Y.^2) + 0.1; % Radius (avoid divide by zero)

% 2. Setup View
axis tight
zlim([-0.5 1])
view(3)
grid on
title('3D Traveling Ripple')

% 3. Animation Loop
for i = 1:100
    t = i * 0.2;
    
    % Calculate Wave Function (Sinc Pulse)
    Z = sin(R - t) ./ R;
    
    % Clear axes to redraw surface
    cla
    
    % Plot Surface
    surf(X, Y, Z)
    
    % Visual Polish
    zlim([-0.5 1])      % Lock Z-axis
    shading interp      % Smooth shading
    colormap jet        % Color map
    
    % Rotate Camera
    % view(Azimuth, Elevation)
    view(30 + t*2, 30)
    
    drawnow
end